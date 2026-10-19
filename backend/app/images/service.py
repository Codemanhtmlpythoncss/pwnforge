"""Base image registry and lifecycle.

Golden images are immutable parents; VM disks are copy-on-write overlays that
reference them. This service tracks image records, verifies checksums, resolves
on-disk paths, and performs *explicit-only* downloads. Nothing here ever runs
automatically — ``fetch_image`` is invoked only by the installer's optional
image step or the ``pwnforge images fetch`` command, and only on the host where
VMs actually run. On a host without the images present, profiles that need
them are reported as ``requires_base_image`` and never as ready.
"""
from __future__ import annotations

import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.database.models import BaseImage, ImageStatus, VMProfile


class ImageError(Exception):
    pass


def list_images(session: Session) -> list[BaseImage]:
    return list(session.execute(select(BaseImage).order_by(BaseImage.key)).scalars())


def get_image(session: Session, key: str) -> BaseImage | None:
    return session.get(BaseImage, key)


def image_path(image: BaseImage) -> Path:
    if image.path:
        return Path(image.path)
    return get_settings().images_dir / f"{image.key}.{image.format}"


def refresh_status(session: Session, image: BaseImage) -> ImageStatus:
    """Reconcile the recorded status with what is actually on disk."""
    p = image_path(image)
    if not p.exists():
        image.status = ImageStatus.absent
        image.actual_size_bytes = 0
    else:
        image.actual_size_bytes = p.stat().st_size
        if image.checksum:
            image.status = ImageStatus.unverified
        else:
            image.status = ImageStatus.present
    session.flush()
    return image.status


def verify_image(session: Session, image: BaseImage) -> bool:
    """Verify checksum of an on-disk image. Returns True if verified/present."""
    p = image_path(image)
    if not p.exists():
        image.status = ImageStatus.absent
        session.flush()
        return False
    if not image.checksum:
        image.status = ImageStatus.present
        session.flush()
        return True
    h = hashlib.new(image.checksum_algo)
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    ok = h.hexdigest().lower() == image.checksum.lower()
    image.status = ImageStatus.present if ok else ImageStatus.corrupt
    image.actual_size_bytes = p.stat().st_size
    session.flush()
    return ok


def fetch_image(session: Session, key: str, *, progress=None, force: bool = False) -> BaseImage:
    """Explicitly download/build a base image. Never called automatically.

    Idempotent: an image already present on disk is left as-is (so re-running a setup or
    update doesn't re-download gigabytes) unless ``force`` is set."""
    image = get_image(session, key)
    if image is None:
        raise ImageError(f"Unknown image {key}")
    if not force and refresh_status(session, image) == ImageStatus.present and verify_image(session, image):
        return image
    if image.source_kind == "build":
        raise ImageError(
            f"Image {key} must be built from its recipe (see build_instructions); "
            "automated building is host-specific and not performed here."
        )
    if not image.source:
        raise ImageError(f"Image {key} has no source URL configured.")
    dest = image_path(image)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.status = ImageStatus.downloading
    session.flush()
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(image.source) as resp, tmp.open("wb") as out:  # noqa: S310
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            while chunk := resp.read(1024 * 256):
                out.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(int(done / total * 100))
        tmp.rename(dest)
    except Exception as exc:  # pragma: no cover - network path
        if tmp.exists():
            tmp.unlink()
        image.status = ImageStatus.absent
        session.flush()
        raise ImageError(f"Download failed for {key}: {exc}") from exc
    image.path = str(dest)
    verify_image(session, image)
    image.updated_at = datetime.now(timezone.utc)
    session.flush()
    return image


def dependents(session: Session, key: str) -> dict:
    """Return everything that depends on an image (profiles + child images)."""
    child_images = list(session.execute(
        select(BaseImage.key).where(BaseImage.parent_key == key)
    ).scalars())
    profiles = list(session.execute(
        select(VMProfile.id).where(VMProfile.base_image_key == key)
    ).scalars())
    return {"child_images": child_images, "profiles": profiles}


def can_delete(session: Session, key: str) -> tuple[bool, str]:
    dep = dependents(session, key)
    if dep["child_images"]:
        return False, f"Image has child images: {dep['child_images']}"
    if dep["profiles"]:
        return False, f"{len(dep['profiles'])} profiles reference this image."
    return True, ""


def validate_chain(session: Session) -> list[str]:
    """Return a list of integrity problems in the image dependency graph."""
    problems: list[str] = []
    images = {i.key: i for i in list_images(session)}
    for img in images.values():
        if img.parent_key and img.parent_key not in images:
            problems.append(f"{img.key}: parent '{img.parent_key}' missing")
    # cycle detection
    for start in images:
        seen, cur = set(), start
        while cur:
            if cur in seen:
                problems.append(f"cycle detected involving {start}")
                break
            seen.add(cur)
            cur = images[cur].parent_key if cur in images else None
    return problems


def storage_summary(session: Session) -> dict:
    images = list_images(session)
    present = [i for i in images if i.status == ImageStatus.present]
    return {
        "total_images": len(images),
        "present": len(present),
        "absent": sum(1 for i in images if i.status == ImageStatus.absent),
        "virtual_bytes": sum(i.virtual_size_bytes for i in images),
        "actual_bytes": sum(i.actual_size_bytes for i in present),
    }
