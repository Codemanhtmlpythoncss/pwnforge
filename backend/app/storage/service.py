"""Storage reporting and copy-on-write overlay management.

Reports *both* allocated virtual capacity and actual physical consumption, and
provides safe (dry-run-first) garbage collection of orphaned overlays. Never
deletes a parent image while a dependent references it.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core import settings_service as cfg
from backend.app.database.models import BaseImage, ImageStatus, VMInstance


def overlays_dir(session: Session) -> Path:
    override = cfg.get_setting(session, "vm.storage_dir")
    if override:
        return Path(override) / "overlays"
    return get_settings().overlays_dir


def _dir_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            continue
    return total


@dataclass
class CleanupItem:
    path: str
    reason: str
    size_bytes: int


def report(session: Session) -> dict:
    s = get_settings()
    disk = shutil.disk_usage(str(s.data_dir))
    images = list(session.execute(select(BaseImage)).scalars())
    present = [i for i in images if i.status == ImageStatus.present]
    ov_dir = overlays_dir(session)
    free_gb = disk.free / 1024 / 1024 / 1024
    warn_gb = int(cfg.get_setting(session, "storage.low_space_warn_gb"))
    return {
        "physical": {
            "data_dir": str(s.data_dir),
            "total_gb": round(disk.total / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "free_gb": round(free_gb, 1),
            "low_space_warning": free_gb < warn_gb,
        },
        "images": {
            "count": len(images),
            "present": len(present),
            "actual_gb": round(sum(i.actual_size_bytes for i in present) / 1024**3, 2),
            "virtual_gb": round(sum(i.virtual_size_bytes for i in images) / 1024**3, 2),
        },
        "overlays": {
            "dir": str(ov_dir),
            "actual_gb": round(_dir_size(ov_dir) / 1024**3, 2),
        },
        "savings_note": (
            "Overlays store only per-VM deltas; N disposable VMs sharing one "
            "golden image consume roughly one base image plus N small overlays, "
            "not N full images."
        ),
    }


def find_orphans(session: Session) -> list[CleanupItem]:
    """Overlay files with no live VM instance referencing them."""
    ov_dir = overlays_dir(session)
    referenced = {
        i.overlay_path for i in session.execute(
            select(VMInstance).where(VMInstance.overlay_path.is_not(None))
        ).scalars()
    }
    orphans: list[CleanupItem] = []
    if ov_dir.exists():
        for p in ov_dir.glob("*.qcow2"):
            if str(p) not in referenced:
                orphans.append(CleanupItem(str(p), "no live instance references this overlay",
                                           p.stat().st_size))
    return orphans


def cleanup(session: Session, *, dry_run: bool = True) -> dict:
    orphans = find_orphans(session)
    removed = []
    freed = 0
    if not dry_run:
        for item in orphans:
            try:
                Path(item.path).unlink()
                removed.append(item.path)
                freed += item.size_bytes
            except OSError:
                continue
    return {
        "dry_run": dry_run,
        "candidates": [vars(o) for o in orphans],
        "removed": removed,
        "freed_bytes": freed,
    }
