"""`pwnforge env`: training environments from the command line (used by host tools such as a homelab dashboard)."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from backend.app.cli import app
from backend.tests.helpers import easy_profile, poll_job

runner = CliRunner()


def _cli(*args):
    r = runner.invoke(app, list(args))
    assert r.exit_code == 0, r.output
    return json.loads(r.output.strip().splitlines()[-1])


def test_env_list_start_stop_delete(admin):
    start = admin.post("/api/vms", json={"profile_id": easy_profile(admin)}).json()
    assert poll_job(admin, start["job_id"])["status"] == "succeeded"
    vmid = start["instance"]["id"]

    listed = _cli("env", "list", "--json")
    row = next(v for v in listed["vms"] if v["id"] == vmid)
    assert row["status"] == "running" and row["memory_mb"] > 0 and row["owner"] == "root"
    assert "password" not in json.dumps(row).lower()

    assert _cli("env", "stop", "vm", vmid)["status"] == "stopped"
    assert _cli("env", "start", "vm", vmid)["status"] == "running"
    assert _cli("env", "delete", "vm", vmid)["ok"] is True
    assert not any(v["id"] == vmid for v in _cli("env", "list", "--json")["vms"])


def test_env_unknown_and_bad_kind(admin):
    assert runner.invoke(app, ["env", "stop", "vm", "nope"]).exit_code == 2
    assert runner.invoke(app, ["env", "stop", "box", "x"]).exit_code == 2


def test_env_cleanup_is_a_dry_run_by_default(admin):
    out = _cli("env", "cleanup")
    assert out["dry_run"] is True and out["removed"] == []


def test_storage_json(admin):
    out = _cli("storage", "--json")
    assert "physical" in out and "overlays" in out
