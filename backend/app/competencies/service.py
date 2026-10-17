"""Competency tracking.

A learner's competency map records a 0-4 level per competency key and the
evidence behind it. Levels only ever rise with demonstrated evidence (passing
assessments, completing labs, finishing lessons). Hint usage alone never
lowers a competency — it is recorded for recommendation nuance only.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competency, UserCompetency

LEVEL_NAMES = {0: "not_started", 1: "beginner", 2: "easy",
               3: "intermediate", 4: "advanced"}


def get_or_create(session: Session, user_id: int, key: str) -> UserCompetency:
    uc = session.execute(
        select(UserCompetency).where(
            UserCompetency.user_id == user_id,
            UserCompetency.competency_key == key)
    ).scalar_one_or_none()
    if uc is None:
        uc = UserCompetency(user_id=user_id, competency_key=key, level=0, evidence_count=0)
        session.add(uc)
        session.flush()
    return uc


def record_evidence(session: Session, user_id: int, key: str, *, level: int) -> UserCompetency:
    """Raise a competency to at least ``level`` and add one evidence point."""
    if not key:
        return None  # type: ignore[return-value]
    uc = get_or_create(session, user_id, key)
    uc.evidence_count += 1
    if level > uc.level:
        uc.level = min(4, level)
    uc.last_demonstrated = datetime.now(timezone.utc)
    session.flush()
    return uc


def competency_map(session: Session, user_id: int) -> list[dict]:
    comps = {c.key: c for c in session.execute(select(Competency)).scalars()}
    user = {uc.competency_key: uc for uc in session.execute(
        select(UserCompetency).where(UserCompetency.user_id == user_id)).scalars()}
    out = []
    for key, comp in sorted(comps.items(), key=lambda kv: (kv[1].domain, kv[1].name)):
        uc = user.get(key)
        out.append({
            "key": key, "name": comp.name, "domain": comp.domain,
            "level": uc.level if uc else 0,
            "level_name": LEVEL_NAMES.get(uc.level if uc else 0, "not_started"),
            "evidence_count": uc.evidence_count if uc else 0,
            "last_demonstrated": uc.last_demonstrated.isoformat()
            if uc and uc.last_demonstrated else None,
        })
    return out


def skills_dashboard(session: Session, user_id: int, mastery_threshold: int = 3) -> dict:
    cmap = competency_map(session, user_id)
    by_domain: dict[str, list[dict]] = {}
    for c in cmap:
        by_domain.setdefault(c["domain"], []).append(c)
    domains = []
    for domain, items in sorted(by_domain.items()):
        mastered = sum(1 for i in items if i["level"] >= mastery_threshold)
        in_progress = sum(1 for i in items if 0 < i["level"] < mastery_threshold)
        domains.append({
            "domain": domain,
            "total": len(items),
            "mastered": mastered,
            "in_progress": in_progress,
            "not_started": sum(1 for i in items if i["level"] == 0),
            "competencies": items,
        })
    return {"domains": domains, "mastery_threshold": mastery_threshold}
