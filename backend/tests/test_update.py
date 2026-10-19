"""The in-app update facility: version reporting, and the opt-in operator command."""
from __future__ import annotations

from backend.tests.conftest import make_user, poll_job


def test_version_is_visible_and_update_is_off_by_default(admin):
    admin.put("/api/settings/admin.update_command", json={"value": ""})
    v = admin.get("/api/admin/version").json()
    assert v["version"] and v["update_enabled"] is False
    # a learner can see the version too, but not trigger an update
    learner, _ = make_user(admin, "learner")
    assert learner.get("/api/admin/version").status_code == 200
    assert learner.post("/api/admin/update").status_code == 403
    # with no command configured, even an admin gets a clear 409
    r = admin.post("/api/admin/update")
    assert r.status_code == 409 and "host" in r.json()["detail"].lower()


def test_update_runs_the_configured_command(admin, tmp_path):
    marker = tmp_path / "updated"
    admin.put("/api/settings/admin.update_command", json={"value": f"echo done > {marker}"})
    assert admin.get("/api/admin/version").json()["update_enabled"] is True
    r = admin.post("/api/admin/update")
    assert r.status_code == 200
    assert poll_job(admin, r.json()["job_id"])["status"] == "succeeded"
    assert marker.read_text().strip() == "done"
    admin.put("/api/settings/admin.update_command", json={"value": ""})


def test_a_failing_update_command_is_reported_not_crashed(admin):
    admin.put("/api/settings/admin.update_command", json={"value": "exit 3"})
    r = admin.post("/api/admin/update")
    assert r.status_code == 200
    job = poll_job(admin, r.json()["job_id"])
    assert job["status"] == "failed" and "exit 3" in job["error"]
    assert admin.get("/api/admin/version").status_code == 200   # server still fine
    admin.put("/api/settings/admin.update_command", json={"value": ""})
