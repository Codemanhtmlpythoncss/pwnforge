"""Authentication & user management service (framework-agnostic)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.models import User, UserRole, UserSession
from backend.app.security import crypto


class AuthError(Exception):
    pass


def count_users(session: Session) -> int:
    return session.execute(select(func.count()).select_from(User)).scalar_one()


def count_users_safe() -> bool:
    """Return True if any user exists (opens its own session; CLI convenience)."""
    from backend.app.database.base import session_scope

    with session_scope() as s:
        return count_users(s) > 0


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.execute(
        select(User).where(func.lower(User.username) == username.lower())
    ).scalar_one_or_none()


def create_user(
    session: Session,
    *,
    username: str,
    password: str,
    role: UserRole = UserRole.learner,
    email: str | None = None,
    display_name: str | None = None,
    must_change_password: bool = False,
    min_password_length: int = 1,
) -> User:
    username = username.strip()
    if not username or len(username) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if get_user_by_username(session, username):
        raise AuthError("Username already exists.")
    if len(password) < max(1, min_password_length):
        raise AuthError(f"Password must be at least {min_password_length} characters.")
    user = User(
        username=username,
        email=email,
        display_name=display_name or username,
        password_hash=crypto.hash_password(password),
        role=role,
        must_change_password=must_change_password,
    )
    session.add(user)
    session.flush()
    return user


def authenticate(session: Session, username: str, password: str) -> User:
    user = get_user_by_username(session, username)
    if not user or not user.is_active:
        # Constant-ish cost even when user is missing.
        crypto.verify_password(password, crypto.hash_password("dummy-not-a-real-hash"))
        raise AuthError("Invalid credentials.")
    if not crypto.verify_password(password, user.password_hash):
        raise AuthError("Invalid credentials.")
    if crypto.needs_rehash(user.password_hash):
        user.password_hash = crypto.hash_password(password)
    user.last_login_at = datetime.now(timezone.utc)
    _bump_streak(user)
    session.flush()
    return user


def change_password(session: Session, user: User, new_password: str, min_length: int = 1) -> None:
    if len(new_password) < max(1, min_length):
        raise AuthError(f"Password must be at least {min_length} characters.")
    user.password_hash = crypto.hash_password(new_password)
    user.must_change_password = False
    # Revoke all other sessions on password change.
    for s in user.sessions:
        s.revoked = True
    session.flush()


def create_session(
    session: Session, user: User, ttl_hours: int, user_agent: str | None, ip: str | None
) -> UserSession:
    us = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        user_agent=(user_agent or "")[:256],
        ip=ip,
    )
    session.add(us)
    session.flush()
    return us


def resolve_session(session: Session, session_id: str) -> User | None:
    us = session.get(UserSession, session_id)
    if us is None or us.revoked:
        return None
    if us.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    user = session.get(User, us.user_id)
    if user is None or not user.is_active:
        return None
    return user


def revoke_session(session: Session, session_id: str) -> None:
    us = session.get(UserSession, session_id)
    if us is not None:
        us.revoked = True
        session.flush()


def _bump_streak(user: User) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if user.last_active_day == today:
        return
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if user.last_active_day == yesterday:
        user.streak_days += 1
    else:
        user.streak_days = 1
    user.last_active_day = today
