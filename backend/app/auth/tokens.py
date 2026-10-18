"""Personal API tokens for the public API (/api/v1) and the AI API (/api/ai).

A token looks like ``pf_<id>_<secret>``. Only SHA-256(secret) is stored, so a
database leak doesn't reveal usable tokens; the full value is returned once, at
creation. Each token carries scopes, never more than its owner's role allows:

  read   status, courses, labs, VMs and lab instances the owner may see
  labs   start, stop and delete the owner's lab instances (learner role or above)
  ai     use the AI assistant

Tokens can't manage tokens, change passwords or use the admin API: those stay
behind an interactive (cookie) session.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import ApiToken, User, UserRole

SCOPES = {"read": "Read status, courses, labs, VMs and your lab instances",
          "labs": "Start, stop and delete your lab instances",
          "ai": "Use the AI assistant"}
MAX_PER_USER = 20
MAX_DAYS = 365
TOKEN_RE = re.compile(r"^pf_([0-9a-f]{32})_([A-Za-z0-9_-]{32,64})$")


class TokenError(Exception):
    pass


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def allowed_scopes(user: User) -> set[str]:
    if user.role == UserRole.viewer:
        return {"read", "ai"}       # viewers look, they don't start machines
    return set(SCOPES)


def create(session: Session, user: User, *, name: str, scopes: list[str], expires_days: int | None) -> tuple[ApiToken, str]:
    name = (name or "").strip()
    if not 1 <= len(name) <= 80:
        raise TokenError("Give the token a name (up to 80 characters).")
    scopes = sorted(set(scopes or []))
    if not scopes:
        raise TokenError("Pick at least one scope.")
    unknown = [s for s in scopes if s not in SCOPES]
    if unknown:
        raise TokenError("Unknown scope: %s." % ", ".join(unknown))
    over = [s for s in scopes if s not in allowed_scopes(user)]
    if over:
        raise TokenError("Your role can't grant: %s." % ", ".join(over))
    if expires_days is not None and not 1 <= int(expires_days) <= MAX_DAYS:
        raise TokenError("Expiry must be 1 to %d days." % MAX_DAYS)
    active = [t for t in session.execute(select(ApiToken).where(ApiToken.user_id == user.id, ApiToken.revoked.is_(False))).scalars()]
    if len(active) >= MAX_PER_USER:
        raise TokenError("You already have %d active tokens; revoke one first." % MAX_PER_USER)
    secret = secrets.token_urlsafe(32)
    row = ApiToken(user_id=user.id, name=name, token_hash=_hash(secret), hint=secret[-4:], scopes=scopes,
                   expires_at=(datetime.now(timezone.utc) + timedelta(days=int(expires_days))) if expires_days else None)
    session.add(row)
    session.flush()
    return row, "pf_%s_%s" % (row.id, secret)


def resolve(session: Session, raw: str) -> tuple[User, ApiToken] | None:
    """(user, token) for a valid, unexpired, unrevoked token of an active user; else None."""
    m = TOKEN_RE.match(raw or "")
    if not m:
        return None
    row = session.get(ApiToken, m.group(1))
    if row is None or row.revoked:
        return None
    if not hmac.compare_digest(row.token_hash, _hash(m.group(2))):
        return None
    now = datetime.now(timezone.utc)
    if row.expires_at is not None and row.expires_at.replace(tzinfo=timezone.utc) < now:
        return None
    user = session.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    if row.last_used_at is None or (now - row.last_used_at.replace(tzinfo=timezone.utc)).total_seconds() > 60:
        row.last_used_at = now           # (at most once a minute: no write per request)
    return user, row


def revoke(session: Session, token_id: str, actor: User) -> ApiToken:
    row = session.get(ApiToken, token_id)
    if row is None or (row.user_id != actor.id and actor.role != UserRole.administrator):
        raise TokenError("No such token.")
    row.revoked = True
    session.flush()
    return row


def listing(session: Session, user: User, everyone: bool = False) -> list[dict]:
    q = select(ApiToken).order_by(ApiToken.created_at.desc())
    if not everyone:
        q = q.where(ApiToken.user_id == user.id)
    return [public(t) for t in session.execute(q).scalars()]


def public(t: ApiToken) -> dict:
    """A token as the API shows it: never the secret or its hash."""
    iso = lambda d: d.isoformat() if d else None  # noqa: E731
    return {"id": t.id, "name": t.name, "user_id": t.user_id, "scopes": t.scopes, "hint": "…" + t.hint,
            "created_at": iso(t.created_at), "expires_at": iso(t.expires_at), "last_used_at": iso(t.last_used_at),
            "revoked": t.revoked}
