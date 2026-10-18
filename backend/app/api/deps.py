"""FastAPI dependencies: DB session, current user, role enforcement."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.auth import service as auth_service
from backend.app.auth import tokens as api_tokens
from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.base import get_session_factory
from backend.app.database.models import User, UserRole
from backend.app.security import crypto, ratelimit

SESSION_COOKIE = "pwnforge_session"


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


TOKEN_PATHS = ("/api/v1/", "/api/ai/")


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    request.state.api_token = None
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        # Allow bearer token for CLI/API clients: a session token, or a personal API token (pf_...).
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
            if token.startswith("pf_"):
                return _api_token_user(request, db, token)
    if not token:
        return None
    sid = crypto.verify_session(token, _session_ttl(db))
    if not sid:
        return None
    return auth_service.resolve_session(db, sid)


def _api_token_user(request: Request, db: Session, raw: str) -> User | None:
    if not request.url.path.startswith(TOKEN_PATHS):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "API tokens work with /api/v1 and /api/ai only; sign in for the rest.")
    found = api_tokens.resolve(db, raw)
    if found is None:
        return None
    user, row = found
    request.state.api_token = row
    return user


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


def token_scopes(request: Request, user: User) -> set[str]:
    """What this request may do: a token's scopes (within its owner's role), or everything the role allows."""
    row = getattr(request.state, "api_token", None)
    allowed = api_tokens.allowed_scopes(user)
    return set(row.scopes) & allowed if row is not None else allowed


def require_scope(scope: str):
    """For the public API: the caller (session or token) must hold `scope`."""
    def dep(request: Request, user: User = Depends(current_user)) -> User:
        if scope not in token_scopes(request, user):
            if getattr(request.state, "api_token", None) is not None:
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"This token doesn't have the '{scope}' scope.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role doesn't allow this.")
        return user
    return dep


def session_only(request: Request, user: User = Depends(current_user)) -> User:
    """Managing credentials needs an interactive session, never an API token."""
    if getattr(request.state, "api_token", None) is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sign in to the website to do this; API tokens can't.")
    return user


def rate_limit(bucket: str, limit: int, window: int):
    """Per-caller rate limit (each token separately, else the signed-in user). Raises 429 with Retry-After."""
    def dep(request: Request, user: User = Depends(current_user)) -> None:
        row = getattr(request.state, "api_token", None)
        who = ("token:" + row.id) if row is not None else ("user:%d" % user.id)
        wait = ratelimit.hit(f"{bucket}:{who}", limit, window)
        if wait:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests; try again shortly.",
                                headers={"Retry-After": str(wait)})
    return dep
