"""Pwnforge public API, version 1 (/api/v1).

A small, stable surface for scripts and tools, built on the same services as the
website. Authenticate with a personal API token (``Authorization: Bearer pf_...``,
created under Developer › API tokens) or a signed-in session. Every route needs
a scope: ``read`` for the GETs, ``labs`` to start, stop or delete lab instances.

Access rules:
  - everyone sees the course catalogue, the lab catalogue and their own VMs, lab
    instances and jobs;
  - instructors and administrators may also *read* other users' lab instances
    (for supervision); only the owner or an administrator may change them;
  - viewers are read-only;
  - another user's instance answers 404, exactly like one that doesn't exist.
Reads are limited to 120 a minute and changes to 20 every 10 minutes, per token
(or per signed-in user). Changes and refused attempts are written to the audit log.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import client_ip, get_db, rate_limit, require_scope
from backend.app.courses import service as courses
from backend.app.database.models import (
    Course, Job, Lab, LabInstance, User, UserRole, VMInstance, VMStatus,
)
from backend.app.jobs import runner
from backend.app.labs import service as labs
from backend.app.networks import service as networks
from backend.app.remote import access as remote_access
from backend.app.security import audit
from backend.app.vms.factory import active_capabilities

router = APIRouter(prefix="/api/v1", tags=["public API v1"])

READ = [Depends(require_scope("read")), Depends(rate_limit("v1-read", 120, 60))]
WRITE = [Depends(require_scope("labs")), Depends(rate_limit("v1-write", 20, 600))]
ID = r"^[0-9a-f]{32}$"
LAB_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,79}$")
API_VERSION = "1.0"


# ---- response models (they make the Swagger page exact) -----------------------------------------
class Who(BaseModel):
    id: int
    username: str
    role: str
    auth: str = Field(description="session or token")
    scopes: list[str]


class Status(BaseModel):
    api_version: str
    version: str
    virtualization: dict[str, Any] = Field(description="Driver and whether real VMs run on this host")
    counts: dict[str, int]
    you: Who


class CourseSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    estimated_minutes: int | None = None


class CourseList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[dict[str, Any]]


class VM(BaseModel):
    id: str
    name: str
    status: str
    profile_id: str | None
    driver: str
    simulated: bool
    ip_address: str | None
    vcpu: int
    memory_mb: int
    lab_instance_id: str | None
    last_error: str | None


class LabSummary(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    machine_count: int
    estimated_minutes: int


class LabInstanceOut(BaseModel):
    id: str
    lab_id: str
    owner_id: int
    status: str
    started_at: str | None
    last_error: str | None
    machines: list[VM]
    networks: list[dict[str, Any]]


class StartLab(BaseModel):
    lab_id: str = Field(..., min_length=1, max_length=80, examples=["web-basics"])


class Started(BaseModel):
    lab_instance_id: str
    job_id: str
    status_url: str


class JobOut(BaseModel):
    id: str
    kind: str
    status: str
    progress: int
    stage: str
    error: str | None


class Ok(BaseModel):
    ok: bool = True
    status: str


# ---- helpers ------------------------------------------------------------------------------------
def _vm(v: VMInstance) -> dict:
    return {"id": v.id, "name": v.name, "status": v.status.value, "profile_id": v.profile_id, "driver": v.driver,
            "simulated": v.driver == "simulation", "ip_address": v.ip_address, "vcpu": v.vcpu, "memory_mb": v.memory_mb,
            "lab_instance_id": v.lab_instance_id, "last_error": v.last_error}


def _instance(db: Session, li: LabInstance) -> dict:
    vms = db.execute(select(VMInstance).where(VMInstance.lab_instance_id == li.id)).scalars()
    return {"id": li.id, "lab_id": li.lab_id, "owner_id": li.owner_id, "status": li.status.value,
            "started_at": li.started_at.isoformat() if li.started_at else None, "last_error": li.last_error,
            "machines": [_vm(v) for v in vms], "networks": networks.topology(db, li.id).get("networks", [])}


def _can_read_all(user: User) -> bool:
    return user.role in (UserRole.administrator, UserRole.instructor)


def _owned_instance(db: Session, request: Request, user: User, li_id: str, *, manage: bool) -> LabInstance:
    """The instance, if this user may see it (manage=False) or change it (manage=True); else 404."""
    li = db.get(LabInstance, li_id)
    ok = li is not None and (li.owner_id == user.id or user.role == UserRole.administrator
                             or (not manage and _can_read_all(user)))
    if not ok:
        if li is not None:      # someone else's: say nothing about it, but keep a record
            audit.record(db, action="api.denied", actor_id=user.id, target_type="lab", target_id=li_id,
                         detail={"manage": manage, "via": "token" if getattr(request.state, "api_token", None) else "session"},
                         ip=client_ip(request))
            db.commit()
        raise HTTPException(404, "Unknown lab instance")
    return li


def _via(request: Request) -> str:
    row = getattr(request.state, "api_token", None)
    return ("token:" + row.id) if row is not None else "session"


# ---- routes -------------------------------------------------------------------------------------
@router.get("/status", response_model=Status, dependencies=READ, summary="Platform status and who you are")
def status(request: Request, user: User = Depends(require_scope("read")), db: Session = Depends(get_db)) -> dict:
    from backend.app.api.deps import token_scopes
    caps = active_capabilities()
    n = lambda q: db.execute(q).scalar_one()  # noqa: E731
    return {
        "api_version": API_VERSION, "version": request.app.version,
        "virtualization": {"driver": caps.driver, "real_virtualization": caps.real_virtualization,
                           "hardware_acceleration": caps.hardware_acceleration},
        "counts": {"courses": n(select(func.count()).select_from(Course)), "labs": n(select(func.count()).select_from(Lab)),
                   "your_running_vms": n(select(func.count()).select_from(VMInstance).where(
                       VMInstance.owner_id == user.id, VMInstance.status == VMStatus.running))},
        "you": {"id": user.id, "username": user.username, "role": user.role.value,
                "auth": "token" if getattr(request.state, "api_token", None) is not None else "session",
                "scopes": sorted(token_scopes(request, user))},
    }


@router.get("/courses", response_model=CourseList, dependencies=READ, summary="List training courses")
def list_courses(q: str | None = Query(None, max_length=100), category: str | None = Query(None, max_length=80),
                 difficulty: str | None = Query(None, max_length=20), tag: str | None = Query(None, max_length=60),
                 limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0, le=100000),
                 db: Session = Depends(get_db)) -> dict:
    return courses.list_courses(db, q=q, category=category, difficulty=difficulty, specialization=None, tag=tag,
                                limit=limit, offset=offset)


@router.get("/courses/{course_id}", dependencies=READ, summary="One course: lessons, exercises (no answers) and your progress")
def course_detail(course_id: str = Path(..., pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$"),
                  user: User = Depends(require_scope("read")), db: Session = Depends(get_db)) -> dict:
    try:
        return courses.get_course_detail(db, course_id, user)
    except courses.CourseError:
        raise HTTPException(404, "Unknown course")


@router.get("/labs", response_model=list[LabSummary], dependencies=READ, summary="The lab catalogue")
def list_labs(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": l.id, "title": l.title, "difficulty": l.difficulty.value, "category": l.category,
             "machine_count": len(l.machines or []), "estimated_minutes": l.estimated_minutes}
            for l in db.execute(select(Lab).order_by(Lab.id)).scalars()]


@router.get("/vms", response_model=list[VM], dependencies=READ, summary="Your virtual machines (administrators: everyone's with all=true)")
def list_vms(all: bool = False, user: User = Depends(require_scope("read")), db: Session = Depends(get_db)) -> list[dict]:
    q = select(VMInstance).where(VMInstance.status != VMStatus.deleted).order_by(VMInstance.created_at.desc())
    if not (all and user.role == UserRole.administrator):
        q = q.where(VMInstance.owner_id == user.id)
    return [_vm(v) for v in db.execute(q).scalars()]


@router.get("/lab-instances", response_model=list[LabInstanceOut], dependencies=READ,
            summary="Your lab instances (instructors and administrators: anyone's with owner_id)")
def list_instances(owner_id: int | None = Query(None, ge=1), user: User = Depends(require_scope("read")),
                   db: Session = Depends(get_db)) -> list[dict]:
    if owner_id is not None and owner_id != user.id and not _can_read_all(user):
        raise HTTPException(403, "Only instructors and administrators can list other users' lab instances.")
    q = select(LabInstance).where(LabInstance.owner_id == (owner_id or user.id), LabInstance.status != VMStatus.deleted)
    return [_instance(db, li) for li in db.execute(q.order_by(LabInstance.created_at.desc())).scalars()]


@router.get("/lab-instances/{li_id}", response_model=LabInstanceOut, dependencies=READ, summary="One lab instance and its machines")
def get_instance(request: Request, li_id: str = Path(..., pattern=ID), user: User = Depends(require_scope("read")),
                 db: Session = Depends(get_db)) -> dict:
    return _instance(db, _owned_instance(db, request, user, li_id, manage=False))


@router.get("/lab-instances/{li_id}/access", dependencies=READ,
            summary="How to reach this instance's machines (no passwords: those are part of the exercise)")
def instance_access(request: Request, li_id: str = Path(..., pattern=ID), user: User = Depends(require_scope("read")),
                    db: Session = Depends(get_db)) -> dict:
    li = _owned_instance(db, request, user, li_id, manage=False)
    return remote_access.connection_details(db, li)


@router.post("/lab-instances", response_model=Started, status_code=202, dependencies=WRITE,
             summary="Start a lab (returns a job to poll)")
def start_instance(body: StartLab, request: Request, user: User = Depends(require_scope("labs")),
                   db: Session = Depends(get_db)) -> dict:
    if not LAB_ID_RE.match(body.lab_id):
        raise HTTPException(422, "lab_id must be a lab's id from /api/v1/labs.")
    if db.get(Lab, body.lab_id) is None:
        raise HTTPException(404, "Unknown lab")
    try:
        li = labs.create_lab_instance(db, lab_id=body.lab_id, owner_id=user.id)
    except labs.LabServiceError as e:
        raise HTTPException(409, str(e))
    audit.record(db, action="api.lab.start", actor_id=user.id, target_type="lab", target_id=li.id,
                 detail={"lab_id": body.lab_id, "via": _via(request)}, ip=client_ip(request))
    db.commit()
    job_id = runner.enqueue("lab.start", params={"lab_instance_id": li.id}, owner_id=user.id, target_type="lab", target_id=li.id)
    return {"lab_instance_id": li.id, "job_id": job_id, "status_url": f"/api/v1/jobs/{job_id}"}


@router.post("/lab-instances/{li_id}/stop", response_model=Ok, dependencies=WRITE, summary="Stop a lab instance (its disks are kept)")
def stop_instance(request: Request, li_id: str = Path(..., pattern=ID), user: User = Depends(require_scope("labs")),
                  db: Session = Depends(get_db)) -> dict:
    li = _owned_instance(db, request, user, li_id, manage=True)
    labs.stop_lab(db, li)
    audit.record(db, action="api.lab.stop", actor_id=user.id, target_type="lab", target_id=li.id,
                 detail={"via": _via(request)}, ip=client_ip(request))
    return {"ok": True, "status": li.status.value}


@router.delete("/lab-instances/{li_id}", response_model=Ok, dependencies=WRITE,
               summary="Delete a lab instance: its machines, disks and networks (course progress is kept)")
def delete_instance(request: Request, li_id: str = Path(..., pattern=ID), user: User = Depends(require_scope("labs")),
                    db: Session = Depends(get_db)) -> dict:
    li = _owned_instance(db, request, user, li_id, manage=True)
    labs.delete_lab_instance(db, li)
    audit.record(db, action="api.lab.delete", actor_id=user.id, target_type="lab", target_id=li_id,
                 detail={"via": _via(request)}, ip=client_ip(request))
    return {"ok": True, "status": "deleted"}


@router.get("/jobs/{job_id}", response_model=JobOut, dependencies=READ, summary="A background job (e.g. a lab starting)")
def get_job(job_id: str = Path(..., pattern=ID), user: User = Depends(require_scope("read")), db: Session = Depends(get_db)) -> dict:
    j = db.get(Job, job_id)
    if j is None or (j.owner_id != user.id and user.role != UserRole.administrator):
        raise HTTPException(404, "Unknown job")
    return {"id": j.id, "kind": j.kind, "status": j.status.value, "progress": j.progress, "stage": j.stage, "error": j.error}
