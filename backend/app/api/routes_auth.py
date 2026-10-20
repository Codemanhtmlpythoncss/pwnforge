"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.api import schemas
from backend.app.api.deps import (
    SESSION_COOKIE, client_ip, current_user, get_db,
)
from backend.app.auth import service as auth_service
from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.models import User, UserRole
from backend.app.security import audit, crypto

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(u: User) -> dict:
    return {"id": u.id, "username": u.username, "display_name": u.display_name,
            "role": u.role.value, "email": u.email, "xp": u.xp,
            "streak_days": u.streak_days,
            "preferred_specialization": u.preferred_specialization,
            "must_change_password": u.must_change_password}


def _set_cookie(response: Response, token: str, db: Session, request: Request) -> None:
    ttl = int(cfg.get_setting(db, "auth.session_ttl_hours", 168)) * 3600
    # Secure flag when served over https; always HttpOnly + SameSite=Lax.
    secure = request.url.scheme == "https"
    response.set_cookie(SESSION_COOKIE, token, max_age=ttl, httponly=True,
                        samesite="lax", secure=secure, path="/")


@router.get("/status")
def auth_status(db: Session = Depends(get_db)) -> dict:
    return {"initialised": auth_service.count_users(db) > 0,
            "registration_open": bool(cfg.get_setting(db, "auth.registration_open"))}


@router.post("/bootstrap")
def bootstrap(body: schemas.BootstrapRequest, request: Request, response: Response,
              db: Session = Depends(get_db)) -> dict:
    """Create the first administrator. Only works when no users exist."""
    if auth_service.count_users(db) > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already initialised")
    minlen = int(cfg.get_setting(db, "auth.min_password_length", 1))
    try:
        user = auth_service.create_user(
            db, username=body.username, password=body.password,
            role=UserRole.administrator, display_name=body.display_name, min_password_length=minlen)
    except auth_service.AuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    us = auth_service.create_session(db, user, int(cfg.get_setting(db, "auth.session_ttl_hours", 168)),
                                     request.headers.get("user-agent"), client_ip(request))
    audit.record(db, action="auth.bootstrap", actor_id=user.id, ip=client_ip(request))
    _set_cookie(response, crypto.sign_session(us.id), db, request)
    return {"user": _user_out(user)}


@router.post("/login")
def login(body: schemas.LoginRequest, request: Request, response: Response,
          db: Session = Depends(get_db)) -> dict:
    try:
        user = auth_service.authenticate(db, body.username, body.password)
    except auth_service.AuthError as e:
        audit.record(db, action="auth.login_failed", detail={"username": body.username},
                     ip=client_ip(request))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    us = auth_service.create_session(db, user, int(cfg.get_setting(db, "auth.session_ttl_hours", 168)),
                                     request.headers.get("user-agent"), client_ip(request))
    audit.record(db, action="auth.login", actor_id=user.id, ip=client_ip(request))
    _set_cookie(response, crypto.sign_session(us.id), db, request)
    return {"user": _user_out(user)}


@router.post("/register")
def register(body: schemas.RegisterRequest, request: Request, response: Response,
             db: Session = Depends(get_db)) -> dict:
    if not bool(cfg.get_setting(db, "auth.registration_open")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is closed")
    minlen = int(cfg.get_setting(db, "auth.min_password_length", 1))
    try:
        user = auth_service.create_user(
            db, username=body.username, password=body.password, email=body.email,
            display_name=body.display_name, role=UserRole.learner, min_password_length=minlen)
    except auth_service.AuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    us = auth_service.create_session(db, user, int(cfg.get_setting(db, "auth.session_ttl_hours", 168)),
                                     request.headers.get("user-agent"), client_ip(request))
    audit.record(db, action="auth.register", actor_id=user.id, ip=client_ip(request))
    _set_cookie(response, crypto.sign_session(us.id), db, request)
    return {"user": _user_out(user)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sid = crypto.verify_session(token, 10**9)
        if sid:
            auth_service.revoke_session(db, sid)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"user": _user_out(user)}


@router.post("/change-password")
def change_password(body: schemas.ChangePasswordRequest, request: Request,
                    user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if not crypto.verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password incorrect")
    minlen = int(cfg.get_setting(db, "auth.min_password_length", 1))
    try:
        auth_service.change_password(db, user, body.new_password, minlen)
    except auth_service.AuthError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    audit.record(db, action="auth.change_password", actor_id=user.id, ip=client_ip(request))
    return {"ok": True}


@router.post("/account/reset")
def reset_account(request: Request, user: User = Depends(current_user),
                  db: Session = Depends(get_db)) -> dict:
    """Wipe the caller's own learning progress for a fresh start.

    Clears XP, streak, course/lesson/assessment progress, skill evidence, captured flags,
    earned achievements and certificates.
    The account, credentials and any running machines are left untouched.
    """
    from sqlalchemy import delete
    from backend.app.database.models import (
        AssessmentProgress, Certificate, CourseProgress, FlagSubmission,
        LessonProgress, UserAchievement, UserCompetency,
    )

    # Clear all learner state, including the idempotency record that prevents repeat
    # assessment XP. Keep the deletes, user update and audit entry in one transaction.
    for model in (AssessmentProgress, LessonProgress, CourseProgress, UserCompetency,
                  FlagSubmission, UserAchievement, Certificate):
        db.execute(delete(model).where(model.user_id == user.id))
    user.xp = 0
    user.streak_days = 0
    user.last_active_day = None
    audit.record(db, action="account.reset", actor_id=user.id, ip=client_ip(request))
    return {"ok": True}
