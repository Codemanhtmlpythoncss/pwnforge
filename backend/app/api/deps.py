"""FastAPI dependencies: DB session, current user, role enforcement."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.auth import service as auth_service
from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.base import get_session_factory
from backend.app.database.models import User, UserRole
from backend.app.security import crypto

SESSION_COOKIE = "hacklab_session"


def get_db(request: Request) -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _session_ttl(session: Session) -> int:
    return int(cfg.get_setting(session, "auth.session_ttl_hours", 168)) * 3600


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        # Allow bearer token for CLI/API clients.
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    sid = crypto.verify_session(token, _session_ttl(db))
    if not sid:
        return None
    return auth_service.resolve_session(db, sid)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = current_user_optional(request, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


def require_roles(*roles: UserRole):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles and user.role != UserRole.administrator:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return dep


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.administrator:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


def client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None
