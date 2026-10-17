"""VM profile catalogue: search, filtering, statistics, readiness, validation."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.database.models import (
    BaseImage, Difficulty, ImageStatus, ProfileReadiness, VMProfile,
)
from backend.app.vms.factory import active_capabilities


def list_profiles(session: Session, *, q: str | None = None, category: str | None = None,
                  difficulty: str | None = None, os_family: str | None = None,
                  arch: str | None = None, readiness: str | None = None,
                  max_memory_mb: int | None = None, max_vcpu: int | None = None,
                  lab_only: bool = False, limit: int = 50, offset: int = 0) -> dict:
    stmt = select(VMProfile)
    count_stmt = select(func.count()).select_from(VMProfile)
    conds = []
    if q:
        like = f"%{q.lower()}%"
        conds.append(or_(func.lower(VMProfile.name).like(like),
                         func.lower(VMProfile.id).like(like)))
    if category:
        conds.append(VMProfile.category == category)
    if difficulty:
        conds.append(VMProfile.difficulty == Difficulty(difficulty))
    if os_family:
        conds.append(VMProfile.os_family == os_family)
    if arch:
        conds.append(VMProfile.arch == arch)
    if readiness:
        conds.append(VMProfile.readiness == ProfileReadiness(readiness))
    if max_memory_mb:
        conds.append(VMProfile.memory_mb <= max_memory_mb)
    if max_vcpu:
        conds.append(VMProfile.vcpu <= max_vcpu)
    if lab_only:
        conds.append(VMProfile.lab_id.is_not(None))
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    total = session.execute(count_stmt).scalar_one()
    rows = list(session.execute(
        stmt.order_by(VMProfile.difficulty, VMProfile.name).limit(limit).offset(offset)
    ).scalars())
    return {"total": total, "items": [summary(p) for p in rows],
            "limit": limit, "offset": offset}


def summary(p: VMProfile) -> dict:
    return {
        "id": p.id, "name": p.name, "category": p.category,
        "difficulty": p.difficulty.value, "level": p.difficulty.level,
        "os_family": p.os_family, "arch": p.arch,
        "base_image_key": p.base_image_key,
        "vcpu": p.vcpu, "memory_mb": p.memory_mb, "disk_gb": p.disk_gb,
        "network_mode": p.network_mode.value,
        "readiness": p.readiness.value,
        "estimated_minutes": p.estimated_minutes, "tags": p.tags,
        "lab_id": p.lab_id, "reset_supported": p.reset_supported,
        "snapshots_supported": p.snapshots_supported, "disposable": p.disposable,
    }


def detail(session: Session, profile_id: str) -> dict:
    p = session.get(VMProfile, profile_id)
    if p is None:
        raise KeyError(profile_id)
    d = summary(p)
    d.update({
        "objectives": p.objectives, "prerequisites": p.prerequisites,
        "packages": p.packages, "services": p.services, "provisioning": p.provisioning,
        "course_ids": p.course_ids, "version": p.version,
    })
    return d


def stats(session: Session) -> dict:
    def group(col):
        return {k: v for k, v in session.execute(
            select(col, func.count()).group_by(col)).all()}

    by_diff = {}
    for d, n in session.execute(
            select(VMProfile.difficulty, func.count()).group_by(VMProfile.difficulty)).all():
        by_diff[d.value] = n
    by_ready = {}
    for r, n in session.execute(
            select(VMProfile.readiness, func.count()).group_by(VMProfile.readiness)).all():
        by_ready[r.value] = n
    total = session.execute(select(func.count()).select_from(VMProfile)).scalar_one()
    return {
        "total": total,
        "by_category": group(VMProfile.category),
        "by_difficulty": by_diff,
        "by_os_family": group(VMProfile.os_family),
        "by_arch": group(VMProfile.arch),
        "by_readiness": by_ready,
        "multi_machine_profiles": session.execute(
            select(func.count()).select_from(VMProfile)
            .where(VMProfile.lab_id.is_not(None))).scalar_one(),
    }


def recompute_readiness(session: Session) -> dict:
    """Recompute each profile's readiness from host capabilities + image state.

    Never marks a profile 'ready' unless its base image is present (real driver)
    or the active driver is a simulation (which needs no real image but is
    flagged as simulated at launch).
    """
    caps = active_capabilities()
    images = {i.key: i for i in session.execute(select(BaseImage)).scalars()}
    host_arch = caps.arch
    counts: dict[str, int] = {}
    for p in session.execute(select(VMProfile)).scalars():
        readiness = _assess(p, images, caps.real_virtualization, host_arch)
        p.readiness = readiness
        counts[readiness.value] = counts.get(readiness.value, 0) + 1
    session.flush()
    return counts


def _assess(p: VMProfile, images: dict, real_virt: bool, host_arch: str) -> ProfileReadiness:
    if not p.base_image_key:
        return ProfileReadiness.requires_manual_config
    img = images.get(p.base_image_key)
    if img is None:
        return ProfileReadiness.invalid
    if not real_virt:
        # Simulation driver: launchable as a simulation regardless of image bytes.
        return ProfileReadiness.ready
    arch_alias = {"x86_64": "amd64", "amd64": "x86_64",
                  "aarch64": "arm64", "arm64": "aarch64"}.get(host_arch, host_arch)
    if p.arch not in (host_arch, arch_alias):
        return ProfileReadiness.unsupported_on_host
    if img.status == ImageStatus.present:
        return ProfileReadiness.ready
    if img.source_kind == "iso":
        return ProfileReadiness.requires_install_media
    return ProfileReadiness.requires_base_image


# Required fields for a valid profile definition.
REQUIRED_FIELDS = ["id", "name", "category", "difficulty", "os_family",
                   "vcpu", "memory_mb", "disk_gb"]


def validate_definition(d: dict) -> list[str]:
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in d:
            errors.append(f"missing field: {f}")
    if "difficulty" in d:
        try:
            Difficulty(d["difficulty"])
        except ValueError:
            errors.append(f"invalid difficulty: {d['difficulty']}")
    for num in ("vcpu", "memory_mb", "disk_gb"):
        if num in d and (not isinstance(d[num], int) or d[num] <= 0):
            errors.append(f"{num} must be a positive integer")
    return errors
