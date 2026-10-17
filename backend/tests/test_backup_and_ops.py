"""Backups, storage reporting, jobs, image registry."""
from __future__ import annotations

import tempfile


def test_backup_create_and_verify():
    from backend.app.maintenance import backup
    out = tempfile.mkdtemp()
    archive = backup.create_backup(out)
    assert archive.endswith(".tar.gz")
    assert backup.verify_backup(archive) is True


def test_storage_report(admin):
    r = admin.get("/api/storage/report").json()
    assert "physical" in r and "images" in r and "overlays" in r
    assert r["physical"]["total_gb"] > 0


def test_image_registry(admin):
    r = admin.get("/api/images").json()
    assert r["summary"]["total_images"] >= 10
    # Debian is the primary foundation and present in the registry.
    keys = [i["key"] for i in r["items"]]
    assert any(k.startswith("debian-13") for k in keys)


def test_image_chain_valid(admin):
    r = admin.get("/api/images/chain/validate").json()
    assert r["problems"] == []


def test_jobs_listed(admin):
    assert "items" in admin.get("/api/jobs").json()


def test_diagnostics(admin):
    d = admin.get("/api/admin/diagnostics").json()
    assert d["counts"]["courses"] >= 50
    assert d["counts"]["profiles"] >= 1000
