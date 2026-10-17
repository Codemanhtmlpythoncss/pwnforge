"""Security: cross-user isolation, terminal authorisation, headers, validation."""
from __future__ import annotations

from backend.tests.helpers import easy_profile, poll_job


def test_cross_user_vm_access_denied(admin, learner):
    prof = easy_profile(admin)
    start = admin.post("/api/vms", json={"profile_id": prof}).json()
    poll_job(admin, start["job_id"])
    vmid = start["instance"]["id"]
    # learner may not see or control the admin's VM
    assert learner.get(f"/api/vms/{vmid}").status_code == 403
    assert learner.post(f"/api/vms/{vmid}/stop").status_code == 403
    assert learner.delete(f"/api/vms/{vmid}").status_code == 403
    admin.delete(f"/api/vms/{vmid}")


def test_learner_only_sees_own_vms(admin, learner):
    assert learner.get("/api/vms").json()["items"] == []


def test_terminal_requires_auth(client):
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    fresh = TestClient(create_app())
    with fresh.websocket_connect("/api/ws/terminal/does-not-exist") as ws:
        msg = ws.receive_text()
        assert "Unauthorised" in msg or "authorised" in msg.lower()


def test_terminal_cross_user_denied(admin, learner):
    prof = easy_profile(admin)
    start = admin.post("/api/vms", json={"profile_id": prof}).json()
    poll_job(admin, start["job_id"])
    vmid = start["instance"]["id"]
    with learner.websocket_connect(f"/api/ws/terminal/{vmid}") as ws:
        msg = ws.receive_text()
        assert "Not authorised" in msg or "authorised" in msg.lower()
    admin.delete(f"/api/vms/{vmid}")


def test_security_headers_present(admin):
    r = admin.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in r.headers


def test_settings_require_admin(learner):
    assert learner.put("/api/settings/ui.theme", json={"value": "light"}).status_code == 403


def test_unknown_setting_rejected(admin):
    assert admin.put("/api/settings/not.a.real.setting", json={"value": 1}).status_code == 400


def test_api_validation_rejects_bad_body(admin):
    assert admin.post("/api/vms", json={}).status_code == 422  # missing profile_id


def test_audit_does_not_store_secrets(admin):
    admin.put("/api/settings/ui.theme", json={"value": "dark"})
    events = admin.get("/api/audit?action=settings.update").json()["items"]
    for e in events:
        assert "***" in str(e["detail"].values()) or "value" not in e["detail"]
