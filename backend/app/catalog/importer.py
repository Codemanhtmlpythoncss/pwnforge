"""Import authored catalogue content into the database.

Idempotent: re-importing upserts content (courses, lessons, profiles, ...)
without touching learner state (progress, competencies, achievements). This
honours the requirement that updating a course must not erase achievements or
progress.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.catalog.content import achievements as ach_content
from backend.app.catalog.content import images as img_content
from backend.app.catalog.content import labs as lab_content
from backend.app.catalog.content import paths as path_content
from backend.app.catalog.content.competencies import COMPETENCIES
from backend.app.catalog.content.courses import ALL_COURSES, validate_unique_ids
from backend.app.catalog.content.profiles import generate_profiles
from backend.app.database.models import (
    Achievement, Assessment, AssessmentQuestion, BaseImage, Competency, Course,
    Difficulty, Exercise, Flag, ImageStatus, Lab, LearningPath, LearningPathStep,
    Lesson, VMProfile,
)
from backend.app.security import crypto


def import_all(session: Session, *, include_profiles: bool = True) -> dict:
    validate_unique_ids()
    counts = {
        "competencies": _import_competencies(session),
        "base_images": _import_images(session),
        "courses": _import_courses(session),
        "learning_paths": _import_paths(session),
        "labs": _import_labs(session),
        "achievements": _import_achievements(session),
    }
    if include_profiles:
        counts["profiles"] = _import_profiles(session)
    session.flush()
    return counts


def _import_competencies(session: Session) -> int:
    existing = {c.key for c in session.execute(select(Competency.key)).scalars()}
    n = 0
    for domain, key, name, desc in COMPETENCIES:
        row = session.get(Competency, key)
        if row is None:
            session.add(Competency(key=key, name=name, domain=domain, description=desc))
            n += 1
        else:
            row.name, row.domain, row.description = name, domain, desc
    return n


def _import_images(session: Session) -> int:
    n = 0
    for d in img_content.BASE_IMAGES:
        row = session.get(BaseImage, d["key"])
        if row is None:
            row = BaseImage(key=d["key"], status=ImageStatus.absent)
            session.add(row)
            n += 1
        row.name = d["name"]
        row.os_family = d["os_family"]
        row.os_version = d["os_version"]
        row.arch = d["arch"]
        row.source_kind = d["source_kind"]
        row.source = d["source"]
        row.parent_key = d["parent"]
        row.virtual_size_bytes = int(d["virtual_gb"] * 1024**3)
        row.build_instructions = d["build"]
    return n


def _import_courses(session: Session) -> int:
    n = 0
    for c in ALL_COURSES:
        course = session.get(Course, c["id"])
        if course is None:
            course = Course(id=c["id"])
            session.add(course)
            n += 1
        course.title = c["title"]
        course.description = c["description"]
        course.difficulty = Difficulty(c["difficulty"])
        course.category = c["category"]
        course.specialization = c["specialization"]
        course.estimated_minutes = c["estimated_minutes"]
        course.objectives = c["objectives"]
        course.prerequisites = c["prerequisites"]
        course.competency_prereqs = c["competency_prereqs"]
        course.tags = c["tags"]
        course.references = c["references"]
        course.os_requirements = c["os_requirements"]
        course.lab_id = c["lab_id"]
        course.version = c["version"]
        session.flush()
        _import_lessons(session, c)
        _import_assessment(session, c)
    return n


def _import_lessons(session: Session, c: dict) -> None:
    for order, l in enumerate(c["lessons"], start=1):
        lid = f"{c['id']}::l{order}"
        lesson = session.get(Lesson, lid)
        if lesson is None:
            lesson = Lesson(id=lid, course_id=c["id"])
            session.add(lesson)
        lesson.order = order
        lesson.title = l["title"]
        lesson.body = l["body"]
        lesson.difficulty = Difficulty(l["difficulty"])
        lesson.estimated_minutes = l["minutes"]
        lesson.competency_key = l["competency"]
        lesson.hints = l["hints"]
        lesson.walkthrough = l["walkthrough"]
        session.flush()
        for eorder, e in enumerate(l["exercises"], start=1):
            eid = f"{lid}::e{eorder}"
            ex = session.get(Exercise, eid)
            if ex is None:
                ex = Exercise(id=eid, lesson_id=lid)
                session.add(ex)
            ex.order = eorder
            # Exercises may be authored via exercise() (has 'title'/'walkthrough')
            # or directly via mcq()/short()/cmd() (question-shaped). Tolerate both.
            ex.title = e.get("title") or (e["prompt"][:60] if e.get("prompt") else f"Exercise {eorder}")
            ex.prompt = e.get("prompt", "")
            ex.kind = e.get("kind", "short_answer")
            spec = {"answer_hash": crypto.hash_answer(e["answer"]) if e.get("answer") else None}
            if e.get("choices"):
                spec["choices"] = [{"text": c2} for c2 in e["choices"]]
            ex.spec = spec
            ex.points = e.get("points", 10)
            ex.competency_key = e.get("competency")
            ex.explanation = e.get("explanation", "")
            ex.hints = [{"text": h} if isinstance(h, str) else h for h in e.get("hints", [])]
            ex.walkthrough = e.get("walkthrough", [])


def _import_assessment(session: Session, c: dict) -> None:
    a = c.get("assessment")
    if not a:
        return
    aid = f"{c['id']}::assessment"
    assessment = session.get(Assessment, aid)
    if assessment is None:
        assessment = Assessment(id=aid, course_id=c["id"])
        session.add(assessment)
    assessment.title = a["title"]
    assessment.description = a["description"]
    assessment.passing_score = a["passing_score"]
    assessment.difficulty = Difficulty(a["difficulty"])
    session.flush()
    for qorder, q in enumerate(a["questions"], start=1):
        qid = f"{aid}::q{qorder}"
        question = session.get(AssessmentQuestion, qid)
        if question is None:
            question = AssessmentQuestion(id=qid, assessment_id=aid)
            session.add(question)
        question.order = qorder
        question.kind = q["kind"]
        question.prompt = q["prompt"]
        question.choices = q.get("choices", [])
        question.answer_hash = crypto.hash_answer(q["answer"])
        question.points = q["points"]
        question.competency_key = q["competency"]
        question.explanation = q["explanation"]
        question.hints = [{"text": h} for h in q.get("hints", [])]


def _import_paths(session: Session) -> int:
    n = 0
    for p in path_content.LEARNING_PATHS:
        path = session.get(LearningPath, p["id"])
        if path is None:
            path = LearningPath(id=p["id"])
            session.add(path)
            n += 1
        path.title = p["title"]
        path.description = p["description"]
        path.specialization = p["specialization"]
        path.difficulty_min = Difficulty(p["difficulty_min"])
        path.difficulty_max = Difficulty(p["difficulty_max"])
        path.tags = p["tags"]
        session.flush()
        # Replace steps (they carry no learner state).
        for existing in list(path.steps):
            session.delete(existing)
        session.flush()
        for s in p["steps"]:
            session.add(LearningPathStep(
                path_id=p["id"], order=s["order"], course_id=s["course_id"],
                lab_id=s["lab_id"], required=s["required"], note=s["note"]))
    return n


def _import_labs(session: Session) -> int:
    n = 0
    for d in lab_content.LABS:
        lab = session.get(Lab, d["id"])
        if lab is None:
            lab = Lab(id=d["id"])
            session.add(lab)
            n += 1
        lab.title = d["title"]
        lab.description = d["description"]
        lab.difficulty = Difficulty(d["difficulty"])
        lab.category = d["category"]
        lab.machines = d["machines"]
        lab.networks = d["networks"]
        lab.startup_order = d["startup_order"]
        lab.readiness_checks = d["readiness_checks"]
        lab.course_id = d["course_id"]
        lab.estimated_minutes = d["estimated_minutes"]
        lab.reset_behavior = d["reset_behavior"]
        lab.objectives = d["objectives"]
        lab.tags = d["tags"]
        # A demo flag per lab enables the submission flow. The plaintext is
        # provisioned into the guest in a real deployment; only the hash is stored.
        fid = f"{d['id']}::flag1"
        flag = session.get(Flag, fid)
        if flag is None:
            flag = Flag(id=fid, scope_type="lab", scope_id=d["id"])
            session.add(flag)
        flag.name = "root flag"
        flag.value_hash = crypto.hash_flag(f"PWN{{{d['id']}}}")
        flag.points = 50
        flag.competency_key = None
    return n


def _import_achievements(session: Session) -> int:
    n = 0
    for d in ach_content.ACHIEVEMENTS:
        row = session.get(Achievement, d["key"])
        if row is None:
            row = Achievement(key=d["key"])
            session.add(row)
            n += 1
        row.title = d["title"]
        row.description = d["description"]
        row.category = d["category"]
        row.points = d["points"]
        row.icon = d["icon"]
        row.criteria = d["criteria"]
    return n


def _import_profiles(session: Session) -> int:
    profiles = generate_profiles()
    existing = {p for p in session.execute(select(VMProfile.id)).scalars()}
    n = 0
    for d in profiles:
        row = session.get(VMProfile, d["id"]) if d["id"] in existing else None
        if row is None:
            row = VMProfile(id=d["id"])
            session.add(row)
            n += 1
        row.name = d["name"]
        row.category = d["category"]
        row.difficulty = Difficulty(d["difficulty"])
        row.os_family = d["os_family"]
        row.arch = d["arch"]
        row.base_image_key = d["base_image_key"]
        row.vcpu = d["vcpu"]
        row.memory_mb = d["memory_mb"]
        row.disk_gb = d["disk_gb"]
        from backend.app.database.models import NetworkMode
        row.network_mode = NetworkMode(d["network_mode"])
        row.packages = d["packages"]
        row.services = d["services"]
        row.provisioning = d["provisioning"]
        row.objectives = d["objectives"]
        row.prerequisites = d["prerequisites"]
        row.estimated_minutes = d["estimated_minutes"]
        row.tags = d["tags"]
        row.reset_supported = d["reset_supported"]
        row.snapshots_supported = d["snapshots_supported"]
        row.disposable = d["disposable"]
        row.lab_id = d["lab_id"]
        row.course_ids = d["course_ids"]
    return n
