"""Course delivery, progress and server-side assessment validation."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, selectinload

from backend.app.competencies import service as competencies
from backend.app.courses import achievements
from backend.app.database.models import (
    Assessment, AssessmentProgress, AssessmentQuestion, Course, CourseProgress,
    Difficulty, Exercise, Lesson, LessonProgress, ProgressStatus, User,
)
from backend.app.security import audit, crypto


class CourseError(Exception):
    pass


# --------------------------------------------------------------------------
# Catalogue queries
# --------------------------------------------------------------------------
def list_courses(session: Session, *, q: str | None = None, category: str | None = None,
                 difficulty: str | None = None, specialization: str | None = None,
                 tag: str | None = None, limit: int = 50, offset: int = 0) -> dict:
    stmt = select(Course)
    count_stmt = select(func.count()).select_from(Course)
    conds = []
    if q:
        like = f"%{q.lower()}%"
        conds.append(or_(func.lower(Course.title).like(like),
                         func.lower(Course.description).like(like),
                         func.lower(Course.id).like(like)))
    if category:
        conds.append(Course.category == category)
    if difficulty:
        conds.append(Course.difficulty == Difficulty(difficulty))
    if specialization:
        conds.append(Course.specialization == specialization)
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    total = session.execute(count_stmt).scalar_one()
    rows = list(session.execute(
        stmt.order_by(Course.difficulty, Course.title).limit(limit).offset(offset)
    ).scalars())
    items = [_course_summary(c) for c in rows]
    if tag:
        items = [c for c in items if tag in c["tags"]]
    return {"total": total, "items": items, "limit": limit, "offset": offset}


def _course_summary(c: Course) -> dict:
    return {
        "id": c.id, "title": c.title, "description": c.description,
        "difficulty": c.difficulty.value, "level": c.difficulty.level,
        "category": c.category, "specialization": c.specialization,
        "estimated_minutes": c.estimated_minutes, "tags": c.tags,
        "prerequisites": c.prerequisites, "objectives": c.objectives,
        "version": c.version,
    }


def get_course_detail(session: Session, course_id: str, user: User | None = None) -> dict:
    course = session.execute(
        select(Course).where(Course.id == course_id)
        .options(selectinload(Course.lessons).selectinload(Lesson.exercises),
                 selectinload(Course.assessments).selectinload(Assessment.questions))
    ).scalar_one_or_none()
    if course is None:
        raise CourseError(f"Unknown course {course_id}")

    lesson_progress: dict[str, LessonProgress] = {}
    cp = None
    if user:
        lesson_progress = {
            lp.lesson_id: lp for lp in session.execute(
                select(LessonProgress).where(LessonProgress.user_id == user.id)).scalars()
        }
        cp = _get_progress(session, user.id, course_id)

    data = _course_summary(course)
    live_percent = None
    effective_status = None
    if cp:
        total_lessons = len(course.lessons)
        completed_lessons = sum(
            1 for lesson in course.lessons
            if lesson_progress.get(lesson.id)
            and lesson_progress[lesson.id].status == ProgressStatus.completed
        )
        live_percent = completed_lessons / total_lessons * 100 if total_lessons else cp.percent
        effective_status = cp.status.value
        if effective_status == ProgressStatus.completed.value and live_percent < 100:
            effective_status = ProgressStatus.in_progress.value
    data.update({
        "references": course.references,
        "competency_prereqs": course.competency_prereqs,
        "lab_id": course.lab_id,
        "lessons": [_lesson_view(l, lesson_progress.get(l.id)) for l in course.lessons],
        "assessments": [_assessment_view(a) for a in course.assessments],
        "progress": _progress_view(cp, status=effective_status, percent=live_percent) if cp else None,
    })
    if user:
        data["prerequisite_status"] = prerequisite_status(session, user, course)
    return data


def _lesson_view(l: Lesson, lp: LessonProgress | None) -> dict:
    return {
        "id": l.id, "order": l.order, "title": l.title, "body": l.body,
        "difficulty": l.difficulty.value, "estimated_minutes": l.estimated_minutes,
        "competency_key": l.competency_key,
        # Optional scaffolding is advertised but content is fetched on demand so
        # it stays hidden until the learner opts in.
        "has_hints": bool(l.hints),
        "hint_count": len(l.hints or []),
        "has_walkthrough": bool(l.walkthrough),
        "walkthrough_step_count": len(l.walkthrough or []),
        "status": lp.status.value if lp else "not_started",
        "hints_used": lp.hints_used if lp else 0,
        "walkthrough_opened": lp.walkthrough_opened if lp else False,
        "exercises": [_exercise_view(e) for e in l.exercises],
    }


def _exercise_view(e: Exercise) -> dict:
    # Never leak the answer hash or which MCQ choice is correct.
    return {
        "id": e.id, "order": e.order, "title": e.title, "prompt": e.prompt,
        "kind": e.kind, "points": e.points,
        "choices": [c.get("text") if isinstance(c, dict) else c for c in (e.spec.get("choices", []))],
        "has_hints": bool(e.hints), "hint_count": len(e.hints or []),
        "has_walkthrough": bool(e.walkthrough),
    }


def _assessment_view(a: Assessment) -> dict:
    return {
        "id": a.id, "title": a.title, "description": a.description,
        "passing_score": a.passing_score, "difficulty": a.difficulty.value,
        "questions": [
            {"id": q.id, "order": q.order, "kind": q.kind, "prompt": q.prompt,
             "choices": q.choices, "points": q.points,
             "has_hints": bool(q.hints), "hint_count": len(q.hints or [])}
            for q in a.questions
        ],
    }


# --------------------------------------------------------------------------
# Prerequisites
# --------------------------------------------------------------------------
def prerequisite_status(session: Session, user: User, course: Course) -> dict:
    unmet_courses = []
    for pid in course.prerequisites or []:
        cp = _get_progress(session, user.id, pid)
        if not cp or cp.status != ProgressStatus.completed:
            unmet_courses.append(pid)
    cmap = {c["key"]: c["level"] for c in competencies.competency_map(session, user.id)}
    unmet_comps = [k for k in (course.competency_prereqs or []) if cmap.get(k, 0) < 1]
    return {
        "met": not unmet_courses and not unmet_comps,
        "unmet_courses": unmet_courses,
        "unmet_competencies": unmet_comps,
    }


# --------------------------------------------------------------------------
# Progress
# --------------------------------------------------------------------------
def _get_progress(session: Session, user_id: int, course_id: str) -> CourseProgress | None:
    return session.execute(
        select(CourseProgress).where(CourseProgress.user_id == user_id,
                                     CourseProgress.course_id == course_id)
    ).scalar_one_or_none()


def _progress_view(cp: CourseProgress, *, status: str | None = None,
                   percent: float | None = None) -> dict:
    return {
        "status": status or cp.status.value,
        "percent": round(cp.percent if percent is None else percent, 1),
        "best_assessment_score": cp.best_assessment_score,
        "started_at": cp.started_at.isoformat() if cp.started_at else None,
        "completed_at": cp.completed_at.isoformat() if cp.completed_at else None,
    }


def start_course(session: Session, user: User, course_id: str) -> CourseProgress:
    course = session.get(Course, course_id)
    if course is None:
        raise CourseError(f"Unknown course {course_id}")
    cp = _get_progress(session, user.id, course_id)
    if cp is None:
        cp = CourseProgress(user_id=user.id, course_id=course_id,
                            status=ProgressStatus.in_progress,
                            started_at=datetime.now(timezone.utc))
        session.add(cp)
    elif cp.status == ProgressStatus.not_started:
        cp.status = ProgressStatus.in_progress
        cp.started_at = datetime.now(timezone.utc)
    session.flush()
    return cp


def complete_lesson(session: Session, user: User, lesson_id: str,
                    hints_used: int = 0, walkthrough_opened: bool = False) -> dict:
    lesson = session.get(Lesson, lesson_id)
    if lesson is None:
        raise CourseError(f"Unknown lesson {lesson_id}")
    lp = session.execute(
        select(LessonProgress).where(LessonProgress.user_id == user.id,
                                     LessonProgress.lesson_id == lesson_id)
    ).scalar_one_or_none()
    if lp is None:
        lp = LessonProgress(user_id=user.id, lesson_id=lesson_id)
        session.add(lp)
    lp.status = ProgressStatus.completed
    lp.hints_used = max(lp.hints_used or 0, hints_used)
    lp.walkthrough_opened = bool(lp.walkthrough_opened) or walkthrough_opened
    lp.completed_at = datetime.now(timezone.utc)
    session.flush()
    # Finishing a lesson is light evidence toward its competency (level 1).
    if lesson.competency_key:
        competencies.record_evidence(session, user.id, lesson.competency_key, level=1)
    start_course(session, user, lesson.course_id)
    recompute_course_percent(session, user, lesson.course_id)
    achievements.evaluate(session, user)
    return {"lesson_id": lesson_id, "status": "completed"}


def reveal_hint(session: Session, user: User, *, lesson_id: str | None = None,
                exercise_id: str | None = None, index: int = 0) -> dict:
    """Return an optional hint and record that it was used (no penalty)."""
    if exercise_id:
        e = session.get(Exercise, exercise_id)
        hints = e.hints if e else []
    else:
        l = session.get(Lesson, lesson_id)
        hints = l.hints if l else []
        if l:
            lp = session.execute(
                select(LessonProgress).where(LessonProgress.user_id == user.id,
                                             LessonProgress.lesson_id == l.id)
            ).scalar_one_or_none()
            if lp is None:
                lp = LessonProgress(user_id=user.id, lesson_id=l.id)
                session.add(lp)
            lp.hints_used = max(lp.hints_used or 0, index + 1)
            session.flush()
    if index < 0 or index >= len(hints or []):
        raise CourseError("No such hint")
    hint = hints[index]
    return {"index": index, "total": len(hints),
            "text": hint.get("text") if isinstance(hint, dict) else hint}


def reveal_assessment_hint(session: Session, assessment_id: str,
                           question_id: str, index: int = 0) -> dict:
    """Reveal one optional question hint without exposing answer metadata."""
    question = session.get(AssessmentQuestion, question_id)
    if question is None or question.assessment_id != assessment_id:
        raise CourseError("Unknown assessment question")
    hints = question.hints or []
    if index < 0 or index >= len(hints):
        raise CourseError("No such hint")
    hint = hints[index]
    return {"question_id": question_id, "index": index, "total": len(hints),
            "text": hint.get("text") if isinstance(hint, dict) else hint}


def reveal_walkthrough(session: Session, user: User, lesson_id: str) -> dict:
    """Return the optional full walkthrough and record that it was opened."""
    l = session.get(Lesson, lesson_id)
    if l is None:
        raise CourseError("Unknown lesson")
    lp = session.execute(
        select(LessonProgress).where(LessonProgress.user_id == user.id,
                                     LessonProgress.lesson_id == l.id)
    ).scalar_one_or_none()
    if lp is None:
        lp = LessonProgress(user_id=user.id, lesson_id=l.id)
        session.add(lp)
    lp.walkthrough_opened = True
    session.flush()
    return {"lesson_id": lesson_id, "steps": l.walkthrough or []}


def recompute_course_percent(session: Session, user: User, course_id: str) -> float:
    lessons = list(session.execute(
        select(Lesson.id).where(Lesson.course_id == course_id)).scalars())
    if not lessons:
        return 0.0
    done = session.execute(
        select(func.count()).select_from(LessonProgress).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id.in_(lessons),
            LessonProgress.status == ProgressStatus.completed)
    ).scalar_one()
    pct = done / len(lessons) * 100
    cp = start_course(session, user, course_id)
    cp.percent = pct
    # Course completion also requires passing assessments if any exist.
    assessments_exist = session.execute(
        select(func.count()).select_from(Assessment).where(Assessment.course_id == course_id)
    ).scalar_one() > 0
    if pct >= 100 and (not assessments_exist or (cp.best_assessment_score or 0) >= 1):
        if cp.status != ProgressStatus.completed:
            cp.status = ProgressStatus.completed
            cp.completed_at = datetime.now(timezone.utc)
            user.xp += 50
    session.flush()
    return pct


# --------------------------------------------------------------------------
# Assessments (server-side validation)
# --------------------------------------------------------------------------
def submit_assessment(session: Session, user: User, assessment_id: str,
                      answers: dict[str, str]) -> dict:
    assessment = session.execute(
        select(Assessment).where(Assessment.id == assessment_id)
        .options(selectinload(Assessment.questions))
    ).scalar_one_or_none()
    if assessment is None:
        raise CourseError(f"Unknown assessment {assessment_id}")

    total_points = sum(q.points for q in assessment.questions) or 1
    earned = 0
    results = []
    for q in assessment.questions:
        given = answers.get(q.id, "")
        correct = _check_answer(q, given)
        if correct:
            earned += q.points
            if q.competency_key:
                competencies.record_evidence(
                    session, user.id, q.competency_key,
                    level=min(4, assessment.difficulty.level))
        results.append({
            "question_id": q.id, "correct": correct,
            "explanation": q.explanation if not correct else "",
        })

    score_pct = earned / total_points * 100
    passed = score_pct >= assessment.passing_score
    cp = start_course(session, user, assessment.course_id)
    norm = score_pct / 100
    cp.best_assessment_score = max(cp.best_assessment_score or 0, norm)
    progress = _get_or_create_assessment_progress(session, user.id, assessment_id)
    progress.best_score = max(progress.best_score or 0, norm)
    progress.passed = bool(progress.passed) or passed
    if passed and not progress.xp_awarded:
        user.xp += 30
        progress.xp_awarded = True
    session.flush()
    recompute_course_percent(session, user, assessment.course_id)
    achievements.evaluate(session, user)
    audit.record(session, action="assessment.submit", actor_id=user.id,
                 target_type="assessment", target_id=assessment_id,
                 detail={"score": round(score_pct, 1), "passed": passed})
    return {
        "assessment_id": assessment_id, "score": round(score_pct, 1),
        "passed": passed, "passing_score": assessment.passing_score,
        "earned": earned, "total": total_points, "results": results,
    }


def _get_or_create_assessment_progress(session: Session, user_id: int,
                                       assessment_id: str) -> AssessmentProgress:
    """Create-or-lock the reward record so duplicate submissions cannot farm XP."""
    bind = session.get_bind()
    values = {
        "user_id": user_id,
        "assessment_id": assessment_id,
        "best_score": 0.0,
        "passed": False,
        "xp_awarded": False,
    }
    if bind.dialect.name == "sqlite":
        stmt = sqlite_insert(AssessmentProgress).values(**values).on_conflict_do_nothing(
            index_elements=["user_id", "assessment_id"]
        )
        session.execute(stmt)
    elif bind.dialect.name == "postgresql":
        stmt = postgresql_insert(AssessmentProgress).values(**values).on_conflict_do_nothing(
            index_elements=["user_id", "assessment_id"]
        )
        session.execute(stmt)
    else:
        progress = session.execute(
            select(AssessmentProgress).where(
                AssessmentProgress.user_id == user_id,
                AssessmentProgress.assessment_id == assessment_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if progress is None:
            progress = AssessmentProgress(**values)
            session.add(progress)
            session.flush()
        return progress

    return session.execute(
        select(AssessmentProgress).where(
            AssessmentProgress.user_id == user_id,
            AssessmentProgress.assessment_id == assessment_id,
        ).with_for_update()
    ).scalar_one()


def _check_answer(q: AssessmentQuestion, given: str) -> bool:
    if q.answer_hash is None:
        return False
    if q.kind == "mcq":
        # given is the choice value/index; hash it the same way it was stored.
        return crypto.constant_time_equals(crypto.hash_answer(str(given)), q.answer_hash)
    return crypto.constant_time_equals(crypto.hash_answer(str(given)), q.answer_hash)


def submit_exercise(session: Session, user: User, exercise_id: str, answer: str) -> dict:
    e = session.get(Exercise, exercise_id)
    if e is None:
        raise CourseError(f"Unknown exercise {exercise_id}")
    expected = e.spec.get("answer_hash")
    correct = bool(expected) and crypto.constant_time_equals(
        crypto.hash_answer(answer), expected)
    if correct and e.competency_key:
        competencies.record_evidence(session, user.id, e.competency_key, level=2)
    return {"exercise_id": exercise_id, "correct": correct,
            "explanation": e.explanation if not correct else ""}
