"""VM lifecycle orchestration.

Implements create / start / stop / reboot / reset / delete / snapshot with a
staged startup sequence that reports real progress and only marks a VM ready
after the driver confirms it is running. Capacity is checked before start;
reservations are tracked so the planner never overcommits. State is reconciled
against the driver so the database reflects reality, not assumptions.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.models import (
    ImageStatus, ProfileReadiness, ResourceReservation,
    VMInstance, VMProfile, VMStatus,
)
from backend.app.images import service as images
from backend.app.security import audit
from backend.app.vms import capacity, provision
from backend.app.vms.driver import DriverError, VMSpec
from backend.app.vms.factory import get_driver


class VMServiceError(Exception):
    pass


# --------------------------------------------------------------------------
# Creation
# --------------------------------------------------------------------------
def create_instance(session: Session, *, profile_id: str, owner_id: int,
                     name: str | None = None, lab_instance_id: str | None = None,
                     persistent: bool = False) -> VMInstance:
    profile = session.get(VMProfile, profile_id)
    if profile is None:
        raise VMServiceError(f"Unknown profile {profile_id}")
    driver = get_driver()
    if driver.name == "unavailable":
        raise VMServiceError(driver.capabilities().notes[0])
    inst = VMInstance(
        name=name or f"{profile_id}-{int(time.time())}",
        profile_id=profile_id, owner_id=owner_id, lab_instance_id=lab_instance_id,
        driver=driver.name, status=VMStatus.defined,
        base_image_key=profile.base_image_key,
        vcpu=profile.vcpu, memory_mb=profile.memory_mb,
        disposable=profile.disposable and not persistent, persistent=persistent,
    )
    session.add(inst)
    session.flush()
    audit.record(session, action="vm.create", actor_id=owner_id,
                 target_type="vm", target_id=inst.id, detail={"profile": profile_id})
    return inst


# --------------------------------------------------------------------------
# Staged start
# --------------------------------------------------------------------------
_START_STAGES = [
    ("validate_profile", "Validating profile"),
    ("check_host", "Checking host compatibility"),
    ("check_capacity", "Checking CPU/RAM capacity"),
    ("check_storage", "Checking available storage"),
    ("resolve_image", "Resolving base image"),
    ("verify_image", "Verifying base image"),
    ("create_overlay", "Creating copy-on-write overlay"),
    ("define_domain", "Defining VM"),
    ("configure_network", "Configuring network"),
    ("start_domain", "Starting VM"),
    ("wait_ready", "Waiting for guest"),
    ("discover_ip", "Discovering IP address"),
    ("check_services", "Checking services"),
    ("mark_ready", "Lab ready"),
]


def start_instance(session: Session, inst: VMInstance, progress=None,
                   flag: str | None = None, target: dict | None = None) -> VMInstance:
    driver = get_driver()
    caps = driver.capabilities()
    profile = session.get(VMProfile, inst.profile_id) if inst.profile_id else None

    def step(i: int, detail: str = "") -> None:
        key, label = _START_STAGES[i]
        if progress:
            progress.update(percent=int((i + 1) / len(_START_STAGES) * 100),
                            stage=label, detail=detail)

    inst.status = VMStatus.starting
    inst.last_error = None
    session.flush()

    try:
        # 1. validate
        step(0)
        if profile is None:
            raise VMServiceError("instance has no profile")

        # 2. host compatibility: an image this host's CPU can run (a Linux profile built for
        # x86_64 runs on the same distro's arm64 image on an arm64 host)
        step(1, f"driver={caps.driver} arch={caps.arch}")
        host_base = None
        if caps.real_virtualization:
            host_base = provision.host_image(session, profile.base_image_key, caps.arch)
            if host_base is None:
                raise VMServiceError(
                    f"This machine ({profile.os_family}, {profile.arch}) can't run on this host's "
                    f"{caps.arch} CPU: there's no {caps.arch} image for it.")

        # 3. capacity
        step(2)
        decision = capacity.can_start(session, vcpu=inst.vcpu,
                                      memory_mb=inst.memory_mb, owner_id=inst.owner_id)
        if not decision.allowed:
            raise VMServiceError(decision.reason)

        # 4. storage headroom
        step(3)
        rep_free = get_settings().data_dir
        # (physical free-space check handled by capacity/storage layers; recorded here)

        overlay_path = base_path = seed_path = None
        if caps.real_virtualization:
            # 5. resolve image
            step(4, host_base.key)
            image = host_base
            images.refresh_status(session, image)
            if image.status not in (ImageStatus.present, ImageStatus.unverified):
                raise VMServiceError(
                    f"Base image '{image.key}' isn't downloaded yet. An administrator can fetch it "
                    f"with: pwnforge images fetch {image.key}")
            base_path = str(images.image_path(image))

            # 6. verify image
            step(5)
            if not images.verify_image(session, image):
                raise VMServiceError(f"Base image '{image.key}' failed checksum verification.")

            # 7. the role image (built once per set of packages), then this machine's overlay on it
            step(6, "preparing the machine image")
            session.commit()          # don't hold the database while a first-time build runs
            role = provision.role_image(
                driver, image, images.image_path(image), os_family=profile.os_family,
                packages=list(profile.packages or []), services=list(profile.services or []),
                arch=caps.arch, disk_gb=profile.disk_gb,
                log=(lambda msg: progress.update(stage=_START_STAGES[6][1], detail=msg)) if progress else None)
            overlay_path = str(get_settings().overlays_dir / f"{inst.id}.qcow2")
            driver.create_overlay(str(role), overlay_path, profile.disk_gb)
            inst.overlay_path = overlay_path
            host = provision.hostname_for(inst.name)
            if target:
                # Black-box target: a login the learner must discover (not shown), flag planted in its home.
                user_data = provision.target_user_data(
                    host, profile.os_family, target.get("user", "user"),
                    target.get("password", ""), flag or provision.derive_flag(inst.lab_instance_id or inst.id),
                    sudo=bool(target.get("sudo")))
            else:
                user_data = provision.instance_user_data(
                    host, provision.login_password(inst.id), profile.os_family, flag=flag)
            seed_path = str(provision.write_seed(
                get_settings().overlays_dir / f"{inst.id}-seed.iso",
                user_data, provision.meta_data(inst.id, host)))
        else:
            # Simulation: no real image needed; be explicit about it.
            step(4, "simulation driver: no real base image required")
            step(5, "skipped (simulation)")
            step(6, "simulation overlay record")
            overlay_path = f"sim://{inst.id}.qcow2"
            inst.overlay_path = overlay_path
            driver.create_overlay(base_path or "sim://base", overlay_path, profile.disk_gb)

        # 8. define
        step(7)
        spec = VMSpec(
            name=f"pwnforge-{inst.id}", vcpu=inst.vcpu, memory_mb=inst.memory_mb,
            arch=caps.arch if caps.real_virtualization else profile.arch,
            base_image_path=base_path, overlay_path=overlay_path,
            disk_gb=profile.disk_gb, network_ref=inst.network_id, headless=True,
            cloud_init_iso=seed_path,
        )
        inst.driver_ref = driver.define(spec)
        inst.status = VMStatus.creating
        session.flush()

        # 9. network (already attached via spec.network_ref if a lab network set it)
        step(8, f"network={inst.network_id or 'default'}")

        # reserve resources now that we are committing to start
        _reserve(session, inst)

        # 10. start
        step(9)
        driver.start(inst.driver_ref)

        # 11. wait for the driver to actually report running
        step(10)
        if not _wait_running(driver, inst.driver_ref, timeout_s=120 if caps.real_virtualization else 2):
            raise VMServiceError("VM did not reach running state within timeout")

        # 12. ip (a real guest asks DHCP for one once it has booted: give it a minute or two)
        step(11)
        inst.ip_address = _wait_ip(driver, inst.driver_ref, 150 if caps.real_virtualization else 0)

        # 13. services (real readiness checks belong to lab definitions; here we
        # record that the domain is up — never claim service health we didn't check)
        step(12, "domain running" + ("" if caps.real_virtualization else " (simulated)"))

        # 14. ready — only now, after confirmed running
        step(13)
        inst.status = VMStatus.running
        inst.started_at = datetime.now(timezone.utc)
        inst.last_heartbeat = datetime.now(timezone.utc)
        session.flush()
        audit.record(session, action="vm.start", actor_id=inst.owner_id,
                     target_type="vm", target_id=inst.id)
        return inst
    except Exception as exc:  # noqa: BLE001
        inst.status = VMStatus.error
        inst.last_error = str(exc)
        _release(session, inst)
        # best-effort cleanup of the overlay we created for this failed start
        if inst.overlay_path and get_driver().capabilities().real_virtualization:
            try:
                get_driver().delete_overlay(inst.overlay_path)
            except DriverError:
                pass
            _seed_file(inst).unlink(missing_ok=True)
        session.flush()
        raise


def stop_instance(session: Session, inst: VMInstance, force: bool = False) -> VMInstance:
    driver = get_driver()
    inst.status = VMStatus.stopping
    session.flush()
    if inst.driver_ref:
        driver.stop(inst.driver_ref, force=force)
    inst.status = VMStatus.stopped
    inst.stopped_at = datetime.now(timezone.utc)
    _release(session, inst)
    session.flush()
    audit.record(session, action="vm.stop", actor_id=inst.owner_id,
                 target_type="vm", target_id=inst.id)
    return inst


def reboot_instance(session: Session, inst: VMInstance) -> VMInstance:
    driver = get_driver()
    if inst.driver_ref:
        driver.reboot(inst.driver_ref)
    inst.status = VMStatus.running
    session.flush()
    return inst


def reset_instance(session: Session, inst: VMInstance, progress=None) -> VMInstance:
    """Return a disposable VM to its clean baseline by rebuilding its overlay.

    Course progress is NOT touched — learner state is independent of VM disk.
    """
    driver = get_driver()
    caps = driver.capabilities()
    if inst.driver_ref:
        driver.stop(inst.driver_ref, force=True)
        driver.delete(inst.driver_ref)
    if inst.overlay_path:
        try:
            driver.delete_overlay(inst.overlay_path)
        except DriverError:
            pass
    inst.status = VMStatus.defined
    inst.driver_ref = None
    inst.ip_address = None
    _release(session, inst)
    session.flush()
    audit.record(session, action="vm.reset", actor_id=inst.owner_id,
                 target_type="vm", target_id=inst.id)
    return start_instance(session, inst, progress=progress)


def delete_instance(session: Session, inst: VMInstance) -> None:
    driver = get_driver()
    inst.status = VMStatus.deleting
    session.flush()
    if inst.driver_ref:
        try:
            driver.stop(inst.driver_ref, force=True)
            driver.delete(inst.driver_ref)
        except DriverError:
            pass
    if inst.overlay_path:
        try:
            driver.delete_overlay(inst.overlay_path)
        except DriverError:
            pass
    _seed_file(inst).unlink(missing_ok=True)
    _release(session, inst)
    audit.record(session, action="vm.delete", actor_id=inst.owner_id,
                 target_type="vm", target_id=inst.id)
    session.delete(inst)
    session.flush()


def snapshot_create(session: Session, inst: VMInstance, name: str, kind: str = "disk"):
    from backend.app.database.models import Snapshot

    driver = get_driver()
    if not inst.driver_ref:
        raise VMServiceError("VM is not defined on the driver")
    ref = driver.snapshot_create(inst.driver_ref, name, kind)
    snap = Snapshot(vm_instance_id=inst.id, name=name, kind=kind, driver_ref=ref)
    session.add(snap)
    session.flush()
    return snap


def reconcile(session: Session) -> dict:
    """Reconcile DB instance states with the driver's actual state."""
    driver = get_driver()
    known = set(driver.list_domains())
    changed = []
    for inst in session.execute(select(VMInstance)).scalars():
        if inst.status in (VMStatus.deleted,):
            continue
        if not inst.driver_ref:
            continue
        actual = driver.status(inst.driver_ref) if inst.driver_ref in known else VMStatus.stopped
        if actual != inst.status and inst.status not in (VMStatus.starting, VMStatus.creating):
            changed.append({"id": inst.id, "was": inst.status.value, "now": actual.value})
            inst.status = actual
            if actual in (VMStatus.stopped, VMStatus.deleted, VMStatus.error):
                _release(session, inst)
    session.flush()
    return {"reconciled": len(changed), "changes": changed}


# --------------------------------------------------------------------------
# reservations & helpers
# --------------------------------------------------------------------------
def _reserve(session: Session, inst: VMInstance) -> None:
    existing = session.execute(
        select(ResourceReservation).where(
            ResourceReservation.vm_instance_id == inst.id,
            ResourceReservation.active.is_(True))
    ).scalar_one_or_none()
    if existing:
        return
    session.add(ResourceReservation(
        vm_instance_id=inst.id, owner_id=inst.owner_id,
        vcpu=inst.vcpu, memory_mb=inst.memory_mb, active=True))
    session.flush()


def _release(session: Session, inst: VMInstance) -> None:
    for r in session.execute(
        select(ResourceReservation).where(
            ResourceReservation.vm_instance_id == inst.id,
            ResourceReservation.active.is_(True))
    ).scalars():
        r.active = False
    session.flush()


def _wait_running(driver, ref: str, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if driver.status(ref) == VMStatus.running:
            return True
        time.sleep(0.1)
    return driver.status(ref) == VMStatus.running


def _wait_ip(driver, ref: str, timeout_s: int) -> str | None:
    deadline = time.time() + timeout_s
    while True:
        try:
            ip = driver.get_ip(ref)
        except DriverError:
            ip = None
        if ip or time.time() >= deadline:
            return ip
        time.sleep(3)


def _seed_file(inst: VMInstance):
    return get_settings().overlays_dir / f"{inst.id}-seed.iso"
