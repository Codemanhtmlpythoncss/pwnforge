"""Audit logging helper. Never records secrets."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.database.models import AuditEvent

_REDACT_KEYS = {"password", "secret", "token", "value", "value_hash", "answer", "flag", "key"}


def _scrub(detail: dict | None) -> dict:
    if not detail:
        return {}
    clean = {}
    for k, v in detail.items():
        if k.lower() in _REDACT_KEYS:
            clean[k] = "***"
        elif isinstance(v, dict):
            clean[k] = _scrub(v)
        else:
            clean[k] = v
    return clean


def record(
    session: Session,
    *,
    action: str,
    actor_id: int | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict | None = None,
    ip: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=_scrub(detail),
        ip=ip,
    )
    session.add(event)
    session.flush()
    return event
