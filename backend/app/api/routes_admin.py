"""Admin, settings, users, dashboard, achievements, audit, diagnostics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api import schemas
from backend.app.api.deps import client_ip, current_user, get_db, require_admin
from backend.app.auth import service as auth_service
from backend.app.core import settings_service as cfg
from backend.app.database.models import (
    Achievement, AuditEvent, Course, CourseProgress, LabInstance, ProgressStatus,
    User, UserAchievement, UserRole, VMInstance, VMProfile, VMStatus,
)
from backend.app.security import audit
from backend.app.vms import service as vms

router = APIRouter(prefix="/api", tags=["admin"])


# ---- Dashboard ----
@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from backend.app.core import host_monitor
    completed = db.execute(select(func.count()).select_from(CourseProgress).where(
        CourseProgress.user_id == user.id,
        CourseProgress.status == ProgressStatus.completed)).scalar_one()
    in_progress = db.execute(select(func.count()).select_from(CourseProgress).where(
        CourseProgress.user_id == user.id,
        CourseProgress.status == ProgressStatus.in_progress)).scalar_one()
    total_courses = db.execute(select(func.count()).select_from(Course)).scalar_one()
    running_vms = db.execute(select(func.count()).select_from(VMInstance).where(
        VMInstance.owner_id == user.id, VMInstance.status == VMStatus.running)).scalar_one()
    active_labs = db.execute(select(func.count()).select_from(LabInstance).where(
        LabInstance.owner_id == user.id, LabInstance.status == VMStatus.running)).scalar_one()
    recent_achievements = [
        {"key": ua.achievement_key, "awarded_at": ua.awarded_at.isoformat()}
        for ua in db.execute(select(UserAchievement).where(
            UserAchievement.user_id == user.id)
            .order_by(UserAchievement.awarded_at.desc()).limit(5)).scalars()]
    recent_activity = [
        {"action": e.action, "target": e.target_id, "at": e.created_at.isoformat()}
        for e in db.execute(select(AuditEvent).where(AuditEvent.actor_id == user.id)
                            .order_by(AuditEvent.created_at.desc()).limit(8)).scalars()]
    vm_failures = db.execute(select(func.count()).select_from(VMInstance).where(
        VMInstance.owner_id == user.id, VMInstance.status == VMStatus.error)).scalar_one()
    return {
        "level": _current_level(db, user),
        "courses_completed": completed, "courses_in_progress": in_progress,
        "courses_total": total_courses, "xp": user.xp, "streak_days": user.streak_days,
        "profiles_available": db.execute(select(func.count()).select_from(VMProfile)).scalar_one(),
        "running_vms": running_vms, "active_labs": active_labs,
        "vm_failures": vm_failures,
        "recent_achievements": recent_achievements, "recent_activity": recent_activity,
        "host": host_monitor.host_stats(),
        "show_streak": bool(cfg.get_setting(db, "ui.show_streak", True)),
        "gamification": bool(cfg.get_setting(db, "ui.gamification", True)),
    }


def _current_level(db: Session, user: User) -> str:
    # Learner's level = highest difficulty of a completed course (or orientation).
    rows = db.execute(
        select(Course.difficulty).join(CourseProgress, CourseProgress.course_id == Course.id)
        .where(CourseProgress.user_id == user.id,
               CourseProgress.status == ProgressStatus.completed)).scalars().all()
    if not rows:
        return "orientation"
    return max(rows, key=lambda d: d.level).value


# ---- Achievements ----
@router.get("/achievements")
def achievements(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    earned = {ua.achievement_key: ua.awarded_at for ua in db.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id)).scalars()}
    out = []
    for a in db.execute(select(Achievement)).scalars():
        out.append({"key": a.key, "title": a.title, "description": a.description,
                    "category": a.category, "points": a.points, "icon": a.icon,
                    "earned": a.key in earned,
                    "awarded_at": earned[a.key].isoformat() if a.key in earned else None})
    return {"items": out}


# ---- Settings ----
@router.get("/settings")
def list_settings(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    rows = cfg.all_settings(db)
    return {"items": [{"key": s.key, "value": s.value, "type": s.value_type,
                       "category": s.category, "description": s.description} for s in rows]}


@router.get("/settings/public")
def public_settings(db: Session = Depends(get_db)) -> dict:
    # UI-relevant settings exposed to all authenticated/anonymous clients.
    keys = ["ui.theme", "ui.gamification", "ui.show_streak", "ui.notifications",
            "ui.hints_enabled", "ui.walkthroughs_enabled", "terminal.scrollback",
            "terminal.font_size"]
    return {k: cfg.get_setting(db, k) for k in keys}


@router.put("/settings/{key}")
def update_setting(key: str, body: schemas.SettingUpdate, request_ip: str | None = None,
                   user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    try:
        row = cfg.set_setting(db, key, body.value, updated_by=user.id)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    audit.record(db, action="settings.update", actor_id=user.id, target_id=key,
                 detail={"value": "***"})
    return {"key": row.key, "value": row.value}


# ---- Users ----
@router.get("/users")
def list_users(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(User)).scalars()
    return {"items": [{"id": u.id, "username": u.username, "role": u.role.value,
                       "is_active": u.is_active, "xp": u.xp,
                       "display_name": u.display_name} for u in rows]}


@router.post("/users")
def create_user(body: schemas.CreateUserRequest, user: User = Depends(require_admin),
                db: Session = Depends(get_db)) -> dict:
    try:
        new = auth_service.create_user(
            db, username=body.username, password=body.password,
            role=UserRole(body.role), email=body.email, display_name=body.display_name,
            must_change_password=True,
            min_password_length=int(cfg.get_setting(db, "auth.min_password_length", 1)))
    except (auth_service.AuthError, ValueError) as e:
        raise HTTPException(400, str(e))
    audit.record(db, action="user.create", actor_id=user.id, target_id=str(new.id))
    return {"id": new.id, "username": new.username, "role": new.role.value}


@router.put("/users/{user_id}")
def update_user(user_id: int, body: schemas.UpdateUserRequest,
                user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "Unknown user")
    if body.role is not None:
        target.role = UserRole(body.role)
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.display_name is not None:
        target.display_name = body.display_name
    if body.preferred_specialization is not None:
        target.preferred_specialization = body.preferred_specialization
    audit.record(db, action="user.update", actor_id=user.id, target_id=str(user_id))
    return {"id": target.id, "role": target.role.value, "is_active": target.is_active}


# ---- Audit ----
@router.get("/audit")
def audit_log(limit: int = 100, action: str | None = None,
              user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    rows = db.execute(stmt).scalars()
    return {"items": [{"id": e.id, "actor_id": e.actor_id, "action": e.action,
                       "target_type": e.target_type, "target_id": e.target_id,
                       "detail": e.detail, "ip": e.ip,
                       "at": e.created_at.isoformat()} for e in rows]}


# ---- Diagnostics / reconcile ----
@router.get("/admin/diagnostics")
def diagnostics(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    from backend.app.vms.detect import probe_host
    from backend.app.images import service as images
    return {
        "host": probe_host(),
        "image_chain_problems": images.validate_chain(db),
        "counts": {
            "users": db.execute(select(func.count()).select_from(User)).scalar_one(),
            "courses": db.execute(select(func.count()).select_from(Course)).scalar_one(),
            "profiles": db.execute(select(func.count()).select_from(VMProfile)).scalar_one(),
            "running_vms": db.execute(select(func.count()).select_from(VMInstance).where(
                VMInstance.status == VMStatus.running)).scalar_one(),
        },
    }


@router.get("/admin/version")
def version(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from backend.app.core import updater
    return updater.version_info(db)


@router.post("/admin/update")
def update(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    from backend.app.core import updater
    from backend.app.jobs import runner

    update_info = updater.version_info(db)
    if not update_info["update_enabled"]:
        raise HTTPException(409, update_info["update_message"])
    audit.record(db, action="admin.update", actor_id=user.id)
    db.commit()
    job_id = runner.enqueue("admin.update", params={}, owner_id=user.id, target_type="system")
    return {"job_id": job_id}


@router.post("/admin/reconcile")
def reconcile(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return vms.reconcile(db)
