"""Learning path progression and next-step resolution."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.database.models import (
    CourseProgress, LearningPath, LearningPathStep, ProgressStatus, User, Course,
)


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
    }


def path_detail(session: Session, path_id: str, user: User | None = None) -> dict:
    p = session.execute(
        select(LearningPath).where(LearningPath.id == path_id)
        .options(selectinload(LearningPath.steps))
    ).scalar_one_or_none()
    if p is None:
        raise KeyError(path_id)

    progress: dict[str, CourseProgress] = {}
    if user:
        progress = {cp.course_id: cp for cp in session.execute(
            select(CourseProgress).where(CourseProgress.user_id == user.id)).scalars()}

    steps = []
    next_step = None
    completed = 0
    for step in sorted(p.steps, key=lambda s: s.order):
        course = session.get(Course, step.course_id) if step.course_id else None
        cp = progress.get(step.course_id) if step.course_id else None
        status = cp.status.value if cp else "not_started"
        if status == "completed":
            completed += 1
        # locked if a prior required step is incomplete
        locked = False
        if user and step.required:
            for prior in steps:
                if prior["required"] and prior["status"] != "completed":
                    locked = True
                    break
        entry = {
            "order": step.order, "course_id": step.course_id, "lab_id": step.lab_id,
            "title": course.title if course else (step.lab_id or "step"),
            "difficulty": course.difficulty.value if course else None,
            "required": step.required, "note": step.note,
            "status": status, "locked": locked,
        }
        steps.append(entry)
        if next_step is None and status != "completed":
            next_step = entry

    return {
        **_summary(p),
        "steps": steps,
        "completed_steps": completed,
        "percent": round(completed / len(steps) * 100, 1) if steps else 0,
        "next_step": next_step,
    }
