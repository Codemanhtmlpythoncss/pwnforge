"""Infrastructure endpoints: profiles, VMs, labs, images, networks, storage, host."""
from __future__ import annotations

import shutil
import socket
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api import schemas
from backend.app.api.deps import current_user, get_db, require_admin
from backend.app.core import host_monitor
from backend.app.core.settings_service import get_setting
from backend.app.database.models import (
    Job, Lab, LabInstance, User, UserRole, VMInstance, VMStatus,
)
from backend.app.images import service as images
from backend.app.jobs import runner
from backend.app.labs import flags as lab_flags
from backend.app.labs import service as labs
from backend.app.networks import service as networks
from backend.app.profiles import service as profiles
from backend.app.storage import service as storage
from backend.app.vms import provision
from backend.app.vms import service as vms
from backend.app.vms.factory import active_capabilities, get_driver

router = APIRouter(prefix="/api", tags=["infra"])


# ---- Host ----
@router.get("/host/stats")
def host_stats(user: User = Depends(current_user)) -> dict:
    return host_monitor.host_stats()


def _host_lan_ip() -> str | None:
    """Best-effort primary IPv4 of this host on its local network (the default-route source).

    Lets the UI fill in the gateway for `ip route add <lab-net> via <host-ip>` instead of a placeholder.
    """
    ip_bin = shutil.which("ip")
    if ip_bin:
        try:
            parts = subprocess.run([ip_bin, "-4", "route", "get", "1.1.1.1"],
                                   capture_output=True, text=True, timeout=2).stdout.split()
            if "src" in parts:
                return parts[parts.index("src") + 1]
        except Exception:  # noqa: BLE001 - best effort; fall back below
            pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))  # no packets sent; just selects the egress interface
            return s.getsockname()[0]
    except Exception:  # noqa: BLE001 - no address to offer
        return None


@router.get("/host/capabilities")
def host_caps(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    c = active_capabilities()
    return {
        "driver": c.driver, "platform": c.platform, "arch": c.arch,
        "cpu_count": c.cpu_count, "total_memory_mb": c.total_memory_mb,
        "real_virtualization": c.real_virtualization,
        "hardware_acceleration": c.hardware_acceleration,
        "features": c.features, "notes": c.notes,
        "host_lan_ip": _host_lan_ip(),
        "lab_network_cidr": get_setting(db, "network.base_cidr", "10.200.0.0/16"),
    }


# ---- Profiles ----
@router.get("/profiles")
def list_profiles(q: str | None = None, category: str | None = None,
                  difficulty: str | None = None, os_family: str | None = None,
                  arch: str | None = None, readiness: str | None = None,
                  max_memory_mb: int | None = None, max_vcpu: int | None = None,
                  lab_only: bool = False, limit: int = Query(50, le=200), offset: int = 0,
                  db: Session = Depends(get_db)) -> dict:
    return profiles.list_profiles(db, q=q, category=category, difficulty=difficulty,
                                  os_family=os_family, arch=arch, readiness=readiness,
                                  max_memory_mb=max_memory_mb, max_vcpu=max_vcpu,
                                  lab_only=lab_only, limit=limit, offset=offset)


@router.get("/profiles/stats")
def profile_stats(db: Session = Depends(get_db)) -> dict:
    return profiles.stats(db)


@router.get("/profiles/{profile_id}")
def profile_detail(profile_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return profiles.detail(db, profile_id)
    except KeyError:
        raise HTTPException(404, "Unknown profile")


# ---- VM instances ----
def _vm_out(i: VMInstance, machine: dict | None = None) -> dict:
    """A machine as its owner (or an administrator) sees it; only those callers reach this.

    ``machine`` is the lab's definition for this box, if any. Explicit black-box targets and
    machines whose role is named ``target`` (including ``target1``/``target2``) never expose
    the provisioned learner login. Practice boxes continue to show their credentials."""
    role = str(machine.get("role") or "").lower() if machine else ""
    is_target = bool(machine and (machine.get("target") or role == "target" or role.startswith("target")))
    out = {"id": i.id, "name": i.name, "profile_id": i.profile_id,
           "status": i.status.value, "driver": i.driver,
           "ip_address": i.ip_address, "vcpu": i.vcpu, "memory_mb": i.memory_mb,
           "disposable": i.disposable, "persistent": i.persistent,
           "lab_instance_id": i.lab_instance_id, "last_error": i.last_error,
           "simulated": i.driver == "simulation", "login": None, "target": is_target}
    if not is_target and i.driver != "simulation" and i.overlay_path:
        out["login"] = {"username": provision.LOGIN_USER, "password": provision.login_password(i.id)}
    return out


def _refresh_ip(db: Session, i: VMInstance) -> None:
    """A real guest gets its address from DHCP after it boots: look it up while it's still unknown."""
    if i.ip_address or i.driver == "simulation" or i.status != VMStatus.running or not i.driver_ref:
        return
    try:
        ip = get_driver().get_ip(i.driver_ref)
    except Exception:  # noqa: BLE001 - best effort; the page asks again
        return
    if ip:
        i.ip_address = ip
        db.commit()


@router.get("/vms")
def list_vms(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(VMInstance).where(VMInstance.owner_id == user.id)).scalars()
    return {"items": [_vm_out(i) for i in rows]}


@router.post("/vms")
def start_vm(body: schemas.StartVMRequest, user: User = Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    if user.role == UserRole.viewer:
        raise HTTPException(403, "Viewers can't start machines.")
    try:
        inst = vms.create_instance(db, profile_id=body.profile_id, owner_id=user.id,
                                   name=body.name, persistent=body.persistent)
    except vms.VMServiceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    job_id = runner.enqueue("vm.start", params={"instance_id": inst.id},
                            owner_id=user.id, target_type="vm", target_id=inst.id)
    return {"instance": _vm_out(inst), "job_id": job_id}


def _owned_vm(db: Session, user: User, vm_id: str) -> VMInstance:
    inst = db.get(VMInstance, vm_id)
    if inst is None:
        raise HTTPException(404, "Unknown VM")
    if inst.owner_id != user.id and user.role.value != "administrator":
        raise HTTPException(403, "Not your VM")
    return inst


@router.get("/vms/{vm_id}")
def get_vm(vm_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return _vm_out(_owned_vm(db, user, vm_id))


@router.post("/vms/{vm_id}/stop")
def stop_vm(vm_id: str, force: bool = False, user: User = Depends(current_user),
            db: Session = Depends(get_db)) -> dict:
    inst = _owned_vm(db, user, vm_id)
    vms.stop_instance(db, inst, force=force)
    return _vm_out(inst)


@router.post("/vms/{vm_id}/reboot")
def reboot_vm(vm_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    inst = _owned_vm(db, user, vm_id)
    vms.reboot_instance(db, inst)
    return _vm_out(inst)


@router.post("/vms/{vm_id}/reset")
def reset_vm(vm_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    inst = _owned_vm(db, user, vm_id)
    db.commit()
    job_id = runner.enqueue("vm.reset", params={"instance_id": inst.id},
                            owner_id=user.id, target_type="vm", target_id=inst.id)
    return {"instance": _vm_out(inst), "job_id": job_id}


@router.post("/vms/{vm_id}/snapshot")
def snapshot_vm(vm_id: str, body: schemas.SnapshotRequest, user: User = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    inst = _owned_vm(db, user, vm_id)
    try:
        snap = vms.snapshot_create(db, inst, body.name, body.kind)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"id": snap.id, "name": snap.name, "kind": snap.kind}


@router.delete("/vms/{vm_id}")
def delete_vm(vm_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    inst = _owned_vm(db, user, vm_id)
    vms.delete_instance(db, inst)
    return {"ok": True}


# ---- Labs ----
@router.get("/labs")
def list_labs(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(Lab)).scalars()
    return {"items": [{"id": l.id, "title": l.title, "description": l.description,
                       "difficulty": l.difficulty.value, "category": l.category,
                       "machine_count": len(l.machines), "estimated_minutes": l.estimated_minutes,
                       "objectives": l.objectives, "tags": l.tags} for l in rows]}


@router.get("/labs/{lab_id}")
def lab_detail(lab_id: str, db: Session = Depends(get_db)) -> dict:
    l = db.get(Lab, lab_id)
    if l is None:
        raise HTTPException(404, "Unknown lab")
    return {"id": l.id, "title": l.title, "description": l.description,
            "difficulty": l.difficulty.value, "category": l.category,
            "machines": l.machines, "networks": l.networks,
            "startup_order": l.startup_order, "objectives": l.objectives,
            "course_id": l.course_id, "estimated_minutes": l.estimated_minutes}


@router.post("/lab-instances")
def start_lab(body: schemas.StartLabRequest, user: User = Depends(current_user),
              db: Session = Depends(get_db)) -> dict:
    if user.role == UserRole.viewer:
        raise HTTPException(403, "Viewers can't start labs.")
    try:
        li = labs.create_lab_instance(db, lab_id=body.lab_id, owner_id=user.id)
    except labs.LabServiceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    job_id = runner.enqueue("lab.start", params={"lab_instance_id": li.id},
                            owner_id=user.id, target_type="lab", target_id=li.id)
    return {"lab_instance_id": li.id, "job_id": job_id}


def _lab_instance_out(db: Session, user: User, li: LabInstance) -> dict:
    vmrows = list(db.execute(select(VMInstance).where(VMInstance.lab_instance_id == li.id)).scalars())
    for v in vmrows:
        _refresh_ip(db, v)
    lab = db.get(Lab, li.lab_id)
    by_role = {m["role"]: m for m in (lab.machines if lab else [])}
    solved = _lab_solved(db, user, li.lab_id)
    return {"id": li.id, "lab_id": li.lab_id, "status": li.status.value,
            "last_error": li.last_error,
            "title": lab.title if lab else li.lab_id,
            "description": lab.description if lab else "",
            "objectives": lab.objectives if lab else [],
            "hints": lab.hints if lab else [],
            "solved": solved,
            # The walkthrough is only revealed once the flag is in (or to an admin).
            "guide": (lab.guide if lab and (solved or user.role.value == "administrator") else None),
            "machines": [_vm_out(v, by_role.get(_role_of(v.name))) for v in vmrows],
            "topology": networks.topology(db, li.id)}


@router.get("/lab-instances")
def list_lab_instances(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(LabInstance).where(LabInstance.owner_id == user.id)).scalars()
    return {"items": [_lab_instance_out(db, user, li) for li in rows]}


@router.get("/lab-instances/{li_id}")
def get_lab_instance(li_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """One instance, for the workspace's frequent polling — avoids rebuilding every other lab each time."""
    li = db.get(LabInstance, li_id)
    if li is None or (li.owner_id != user.id and user.role.value != "administrator"):
        raise HTTPException(404, "Unknown lab instance")
    return _lab_instance_out(db, user, li)


def _lab_solved(db: Session, user: User, lab_id: str) -> bool:
    from backend.app.database.models import Flag, FlagSubmission
    fid = db.execute(select(Flag.id).where(Flag.scope_type == "lab", Flag.scope_id == lab_id)).scalars().first()
    if not fid:
        return False
    return db.execute(select(FlagSubmission).where(
        FlagSubmission.user_id == user.id, FlagSubmission.flag_id == fid,
        FlagSubmission.correct.is_(True))).first() is not None


def _role_of(name: str) -> str:
    return name.split("-", 1)[1] if "-" in name else name


@router.post("/lab-instances/{li_id}/stop")
def stop_lab(li_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    li = db.get(LabInstance, li_id)
    if li is None or (li.owner_id != user.id and user.role.value != "administrator"):
        raise HTTPException(404, "Unknown lab instance")
    labs.stop_lab(db, li)
    return {"ok": True}


@router.delete("/lab-instances/{li_id}")
def delete_lab(li_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    li = db.get(LabInstance, li_id)
    if li is None or (li.owner_id != user.id and user.role.value != "administrator"):
        raise HTTPException(404, "Unknown lab instance")
    labs.delete_lab_instance(db, li)
    return {"ok": True}


@router.post("/flags/submit")
def submit_flag(body: schemas.SubmitFlagRequest, user: User = Depends(current_user),
                db: Session = Depends(get_db)) -> dict:
    return lab_flags.submit_flag(db, user, scope_type=body.scope_type,
                                 scope_id=body.scope_id, value=body.value)


# ---- Images (admin for fetch/prune) ----
@router.get("/images")
def list_images(db: Session = Depends(get_db)) -> dict:
    out = []
    for img in images.list_images(db):
        out.append({"key": img.key, "name": img.name, "os_family": img.os_family,
                    "os_version": img.os_version, "arch": img.arch, "status": img.status.value,
                    "parent_key": img.parent_key, "source_kind": img.source_kind,
                    "virtual_gb": round(img.virtual_size_bytes / 1024**3, 1),
                    "actual_gb": round(img.actual_size_bytes / 1024**3, 2)})
    return {"items": out, "summary": images.storage_summary(db)}


@router.post("/images/{key}/verify")
def verify_image(key: str, user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    img = images.get_image(db, key)
    if img is None:
        raise HTTPException(404, "Unknown image")
    ok = images.verify_image(db, img)
    return {"key": key, "verified": ok, "status": img.status.value}


@router.post("/images/{key}/fetch")
def fetch_image(key: str, user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    img = images.get_image(db, key)
    if img is None:
        raise HTTPException(404, "Unknown image")
    db.commit()
    job_id = runner.enqueue("image.fetch", params={"key": key}, owner_id=user.id,
                            target_type="image", target_id=key)
    return {"job_id": job_id, "note": "Download runs on this host only when invoked."}


@router.get("/images/chain/validate")
def validate_chain(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return {"problems": images.validate_chain(db)}


# ---- Networks ----
@router.get("/networks")
def list_networks(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from backend.app.database.models import VirtualNetwork
    rows = db.execute(select(VirtualNetwork)).scalars()
    return {"items": [{"id": n.id, "name": n.name, "mode": n.mode.value, "cidr": n.cidr,
                       "external": n.external_access, "lab_instance_id": n.lab_instance_id}
                      for n in rows]}


# ---- Storage ----
@router.get("/storage/report")
def storage_report(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return storage.report(db)


@router.post("/storage/cleanup")
def storage_cleanup(dry_run: bool = True, user: User = Depends(require_admin),
                    db: Session = Depends(get_db)) -> dict:
    return storage.cleanup(db, dry_run=dry_run)


# ---- Jobs ----
@router.get("/jobs/{job_id}")
def get_job(job_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    job = db.get(Job, job_id)
    if job is None or (job.owner_id != user.id and user.role != UserRole.administrator):
        raise HTTPException(404, "Unknown job")
    return {"id": job.id, "kind": job.kind, "status": job.status.value,
            "progress": job.progress, "stage": job.stage, "steps": job.steps,
            "error": job.error, "result": job.result}


@router.get("/jobs")
def list_jobs(limit: int = 25, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    q = select(Job).order_by(Job.created_at.desc()).limit(max(1, min(limit, 200)))
    if user.role != UserRole.administrator:
        q = q.where(Job.owner_id == user.id)
    rows = db.execute(q).scalars()
    return {"items": [{"id": j.id, "kind": j.kind, "status": j.status.value,
                       "progress": j.progress, "stage": j.stage} for j in rows]}
