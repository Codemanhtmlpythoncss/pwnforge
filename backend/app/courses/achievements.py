"""Achievement evaluation. Achievements reflect real completion criteria only."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.models import (
    Achievement, CourseProgress, ProgressStatus, UserAchievement,
    UserCompetency, User, LabInstance, VMStatus,
)


def _already(session: Session, user_id: int, key: str) -> bool:
    return session.execute(
        select(func.count()).select_from(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_key == key)
    ).scalar_one() > 0


def _courses_completed(session: Session, user_id: int) -> int:
    return session.execute(
        select(func.count()).select_from(CourseProgress).where(
            CourseProgress.user_id == user_id,
            CourseProgress.status == ProgressStatus.completed)
    ).scalar_one()


def _mastered_in_domain(session: Session, user_id: int, domain: str, threshold: int = 3) -> int:
    from backend.app.database.models import Competency

    keys = [c.key for c in session.execute(
        select(Competency).where(Competency.domain == domain)).scalars()]
    if not keys:
        return 0
    return session.execute(
        select(func.count()).select_from(UserCompetency).where(
            UserCompetency.user_id == user_id,
            UserCompetency.competency_key.in_(keys),
            UserCompetency.level >= threshold)
    ).scalar_one()


def _labs_completed(session: Session, user_id: int) -> int:
    return session.execute(
        select(func.count()).select_from(LabInstance).where(
            LabInstance.owner_id == user_id,
            LabInstance.status == VMStatus.running)
    ).scalar_one()


def evaluate(session: Session, user: User) -> list[str]:
    """Award any newly-earned achievements. Returns keys awarded this call."""
    awarded: list[str] = []
    for ach in session.execute(select(Achievement)).scalars():
        if _already(session, user.id, ach.key):
            continue
        if _criteria_met(session, user, ach.criteria or {}):
            session.add(UserAchievement(user_id=user.id, achievement_key=ach.key,
                                        awarded_at=datetime.now(timezone.utc)))
            user.xp += ach.points
            awarded.append(ach.key)
    if awarded:
        session.flush()
    return awarded


def _criteria_met(session: Session, user: User, crit: dict) -> bool:
    ctype = crit.get("type")
    if ctype == "courses_completed":
        return _courses_completed(session, user.id) >= int(crit.get("count", 1))
    if ctype == "competency_mastered_domain":
        return _mastered_in_domain(session, user.id, crit["domain"],
                                   int(crit.get("threshold", 3))) >= int(crit.get("count", 1))
    if ctype == "labs_completed":
        return _labs_completed(session, user.id) >= int(crit.get("count", 1))
    if ctype == "xp_reached":
        return user.xp >= int(crit.get("amount", 100))
    if ctype == "streak_days":
        return user.streak_days >= int(crit.get("days", 3))
    return False
