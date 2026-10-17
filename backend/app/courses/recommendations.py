"""Next-step recommendations based on demonstrated competency and prerequisites."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.competencies import service as competencies
from backend.app.courses import service as courses
from backend.app.database.models import (
    Course, CourseProgress, Difficulty, ProgressStatus, User,
)


def recommend(session: Session, user: User, limit: int = 5) -> list[dict]:
    progress = {
        cp.course_id: cp for cp in session.execute(
            select(CourseProgress).where(CourseProgress.user_id == user.id)).scalars()
    }
    cmap = {c["key"]: c["level"] for c in competencies.competency_map(session, user.id)}
    all_courses = list(session.execute(select(Course)).scalars())

    scored: list[tuple[float, Course, dict]] = []
    for c in all_courses:
        cp = progress.get(c.id)
        if cp and cp.status == ProgressStatus.completed:
            continue
        prereq = courses.prerequisite_status(session, user, c)
        score = 0.0
        reasons = []
        if cp and cp.status == ProgressStatus.in_progress:
            score += 100
            reasons.append("resume in-progress course")
        if prereq["met"]:
            score += 40
            reasons.append("prerequisites met")
        else:
            score -= 25 * (len(prereq["unmet_courses"]) + len(prereq["unmet_competencies"]))
            reasons.append("has unmet prerequisites")
        # Prefer courses near the learner's current competency frontier.
        if user.preferred_specialization and c.specialization == user.preferred_specialization:
            score += 30
            reasons.append(f"matches specialization {c.specialization}")
        # Lower difficulty first when the learner is early.
        avg_level = (sum(cmap.values()) / len(cmap)) if cmap else 0
        score += max(0, 20 - abs(c.difficulty.level - (avg_level + 1)) * 6)
        scored.append((score, c, {"reasons": reasons, "prerequisites": prereq}))

    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, c, meta in scored[:limit]:
        out.append({
            "course": courses._course_summary(c),
            "score": round(score, 1),
            "reasons": meta["reasons"],
            "prerequisites": meta["prerequisites"],
        })
    return out
