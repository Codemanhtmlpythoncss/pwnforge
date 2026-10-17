"""Flag submission with server-side validation.

Only salted hashes of flags are stored; the plaintext never ships to the
browser and the only way to earn points is a correct server-side match.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.competencies import service as competencies
from backend.app.database.models import Flag, FlagSubmission, User
from backend.app.security import audit, crypto


def submit_flag(session: Session, user: User, *, scope_type: str, scope_id: str,
                value: str) -> dict:
    flags = list(session.execute(
        select(Flag).where(Flag.scope_type == scope_type, Flag.scope_id == scope_id)
    ).scalars())
    submitted = crypto.hash_flag(value)
    matched = None
    for f in flags:
        if crypto.constant_time_equals(submitted, f.value_hash):
            matched = f
            break

    already = False
    if matched:
        already = session.execute(
            select(FlagSubmission).where(
                FlagSubmission.user_id == user.id,
                FlagSubmission.flag_id == matched.id,
                FlagSubmission.correct.is_(True))
        ).scalar_one_or_none() is not None

    # Record the attempt only against a real flag row (FK integrity); an
    # incorrect attempt is logged against the scope's first flag.
    record_flag_id = matched.id if matched else (flags[0].id if flags else None)
    if record_flag_id is not None:
        session.add(FlagSubmission(user_id=user.id, flag_id=record_flag_id,
                                   correct=bool(matched)))
    if matched and not already:
        user.xp += matched.points
        if matched.competency_key:
            competencies.record_evidence(session, user.id, matched.competency_key, level=3)
    session.flush()
    audit.record(session, action="flag.submit", actor_id=user.id,
                 target_type=scope_type, target_id=scope_id,
                 detail={"correct": bool(matched)})
    return {
        "correct": bool(matched),
        "points": matched.points if (matched and not already) else 0,
        "already_solved": already,
        "name": matched.name if matched else None,
    }
