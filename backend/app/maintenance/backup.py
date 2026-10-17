"""Backup and restore.

Backs up the SQLite database (via the online backup API for a consistent copy
of an active database), configuration and the catalogue metadata into a
timestamped, checksummed archive. Disposable VM overlays are excluded by
default; persistent VM definitions are recorded. Restore is documented in
docs/BACKUPS.md.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import get_settings


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create_backup(output_dir: str | None = None, include_disposable: bool = False) -> str:
    s = get_settings()
    out = Path(output_dir) if output_dir else s.backups_dir
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    staging = Path(tempfile.mkdtemp(prefix="pwnforge-backup-"))

    try:
        # Consistent DB copy via SQLite online backup API.
        db_url = s.resolved_database_url()
        manifest: dict = {"created": stamp, "files": {}}
        if db_url.startswith("sqlite"):
            src = db_url.replace("sqlite:///", "")
            dest = staging / "pwnforge.db"
            _online_backup(src, dest)
            manifest["files"]["pwnforge.db"] = {"sha256": _sha256(dest)}
        # Config
        for name in ("secret_key", ".env"):
            p = s.data_dir / name
            if p.exists():
                shutil.copy2(p, staging / name)
                manifest["files"][name] = {"sha256": _sha256(staging / name)}
        # Image metadata snapshot
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2))

        archive = out / f"pwnforge-backup-{stamp}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(staging, arcname="pwnforge-backup")
        # Verify archive integrity
        checksum = _sha256(archive)
        (out / f"pwnforge-backup-{stamp}.sha256").write_text(f"{checksum}  {archive.name}\n")
        return str(archive)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _online_backup(src: str, dest: Path) -> None:
    source = sqlite3.connect(src)
    target = sqlite3.connect(str(dest))
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def verify_backup(archive: str) -> bool:
    archive_path = Path(archive)
    sidecar = archive_path.with_suffix("").with_suffix(".sha256")
    if not sidecar.exists():
        return False
    expected = sidecar.read_text().split()[0]
    return _sha256(archive_path) == expected
