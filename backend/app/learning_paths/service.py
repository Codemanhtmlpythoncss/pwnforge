"""Learning path progression, next-step resolution, and completion certificates."""
from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.database.models import (
    Certificate, CourseProgress, Lab, LabTaskSubmission, LearningPath, LearningPathStep,
    ProgressStatus, User, Course,
)


def _solved_lab_ids(session: Session, user_id: int) -> set[str]:
    """Lab ids this user has captured the flag for (a correct, lab-scoped submission)."""
    from backend.app.database.models import Flag, FlagSubmission

    rows = session.execute(
        select(Flag.scope_id).select_from(FlagSubmission).join(Flag, Flag.id == FlagSubmission.flag_id).where(
            FlagSubmission.user_id == user_id, FlagSubmission.correct.is_(True), Flag.scope_type == "lab")
    ).scalars()
    return set(rows)


def _cert_out(c: Certificate) -> dict:
    return {"serial": c.serial, "path_id": c.path_id, "path_title": c.path_title,
            "recipient": c.recipient, "issued_at": c.issued_at.isoformat()}


def issue_if_complete(session: Session, user: User, path_id: str, percent: float) -> Certificate | None:
    """Issue a certificate once a path is 100% complete (idempotent — one per user+path)."""
    if percent < 100 or user is None:
        return None
    existing = session.execute(
        select(Certificate).where(Certificate.user_id == user.id, Certificate.path_id == path_id)
    ).scalar_one_or_none()
    if existing:
        return existing
    p = session.get(LearningPath, path_id)
    cert = Certificate(serial="PF-" + secrets.token_hex(6).upper(), user_id=user.id, path_id=path_id,
                       recipient=user.display_name or user.username, path_title=p.title if p else path_id)
    session.add(cert)
    session.flush()
    return cert


def list_certificates(session: Session, user: User) -> list[dict]:
    rows = session.execute(
        select(Certificate).where(Certificate.user_id == user.id).order_by(Certificate.issued_at.desc())
    ).scalars()
    return [_cert_out(c) for c in rows]


def verify_certificate(session: Session, serial: str) -> dict | None:
    c = session.execute(select(Certificate).where(Certificate.serial == serial)).scalar_one_or_none()
    return _cert_out(c) if c else None


def list_paths(session: Session) -> list[dict]:
    paths = list(session.execute(
        select(LearningPath).options(selectinload(LearningPath.steps))
        .order_by(LearningPath.title)).scalars())
    return [_summary(p) for p in paths]


def _summary(p: LearningPath) -> dict:
    return {
        "id": p.id, "title": p.title, "description": p.description,
        "specialization": p.specialization,
        "difficulty_min": p.difficulty_min.value, "difficulty_max": p.difficulty_max.value,
        "tags": p.tags, "step_count": len(p.steps),
        "outcomes": p.outcomes or [], "capstone": p.capstone or {},
    }


def path_detail(session: Session, path_id: str, user: User | None = None) -> dict:
    p = session.execute(
        select(LearningPath).where(LearningPath.id == path_id)
        .options(selectinload(LearningPath.steps))
    ).scalar_one_or_none()
    if p is None:
        raise KeyError(path_id)

    course_ids = {step.course_id for step in p.steps if step.course_id}
    lab_ids = {step.lab_id for step in p.steps if step.lab_id}
    courses = {course.id: course for course in session.execute(
        select(Course).where(Course.id.in_(course_ids))).scalars()} if course_ids else {}
    labs = {lab.id: lab for lab in session.execute(
        select(Lab).where(Lab.id.in_(lab_ids))).scalars()} if lab_ids else {}
    progress: dict[str, CourseProgress] = {}
    solved_labs: set[str] = set()
    completed_lab_tasks: dict[str, set[str]] = {}
    if user:
        progress = {cp.course_id: cp for cp in session.execute(
            select(CourseProgress).where(CourseProgress.user_id == user.id,
                                         CourseProgress.course_id.in_(course_ids))).scalars()} if course_ids else {}
        solved_labs = _solved_lab_ids(session, user.id)
        if lab_ids:
            for lab_id, task_id in session.execute(
                select(LabTaskSubmission.lab_id, LabTaskSubmission.task_id).where(
                    LabTaskSubmission.user_id == user.id,
                    LabTaskSubmission.lab_id.in_(lab_ids),
                )
            ):
                completed_lab_tasks.setdefault(lab_id, set()).add(task_id)

    steps = []
    next_step = None
    completed = 0
    completed_required = 0
    required_count = 0
    for step in sorted(p.steps, key=lambda s: s.order):
        course = courses.get(step.course_id) if step.course_id else None
        lab = labs.get(step.lab_id) if step.lab_id else None
        cp = progress.get(step.course_id) if step.course_id else None
        if step.lab_id:
            # Guided labs require both the worksheet and flag; legacy labs have no worksheet.
            lab_tasks = list(lab.tasks or []) if lab else []
            completed_tasks = completed_lab_tasks.get(step.lab_id, set())
            worksheet_done = all(task["id"] in completed_tasks for task in lab_tasks)
            if step.lab_id in solved_labs and worksheet_done:
                status = "completed"
            elif step.lab_id in solved_labs or completed_tasks:
                status = "in_progress"
            else:
                status = "not_started"
        else:
            status = cp.status.value if cp else "not_started"
            if cp and status == ProgressStatus.completed.value and cp.percent < 100:
                status = ProgressStatus.in_progress.value
        if status == "completed":
            completed += 1
        if step.required:
            required_count += 1
            if status == "completed":
                completed_required += 1
        # locked if a prior required step is incomplete
        locked = False
        if user and step.required:
            for prior in steps:
                if prior["required"] and prior["status"] != "completed":
                    locked = True
                    break
        entry = {
            "order": step.order, "course_id": step.course_id, "lab_id": step.lab_id,
            "title": course.title if course else (lab.title if lab else (step.lab_id or "step")),
            "difficulty": (course.difficulty.value if course
                           else lab.difficulty.value if lab else None),
            "kind": "lab" if step.lab_id else "course",
            "required": step.required, "note": step.note,
            "status": status, "locked": locked,
        }
        steps.append(entry)
        if next_step is None and status != "completed":
            next_step = entry

    # Optional warm-ups are useful, but don't block the learning-path certificate.
    percent = round(completed_required / required_count * 100, 1) if required_count else 0
    if percent >= 100:
        next_step = None
    cert = issue_if_complete(session, user, p.id, percent) if user else None
    return {
        **_summary(p),
        "steps": steps,
        "completed_steps": completed,
        "completed_required_steps": completed_required,
        "required_step_count": required_count,
        "percent": percent,
        "next_step": next_step,
        "certificate": _cert_out(cert) if cert else None,
    }
