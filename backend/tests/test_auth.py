"""Authentication and authorisation."""
from __future__ import annotations


def test_bootstrap_then_second_bootstrap_rejected(admin):
    r = admin.post("/api/auth/bootstrap", json={"username": "another", "password": "yyyyyyyyyy"})
    assert r.status_code == 409  # already initialised


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "root", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    fresh = TestClient(create_app())
    assert fresh.get("/api/auth/me").status_code == 401


def test_learner_cannot_access_admin(learner):
    assert learner.get("/api/settings").status_code == 403
    assert learner.get("/api/users").status_code == 403
    assert learner.get("/api/audit").status_code == 403


def test_admin_can_access_admin(admin):
    assert admin.get("/api/settings").status_code == 200
    assert admin.get("/api/users").status_code == 200


def test_password_hash_not_leaked(admin):
    me = admin.get("/api/auth/me").json()["user"]
    assert "password" not in me and "password_hash" not in me


def test_password_min_length_enforced(admin):
    # 9 chars passes the schema (>=8) but fails the service policy (>=10) -> 400.
    r = admin.post("/api/users", json={"username": "shorty", "password": "ninechar9", "role": "learner"})
    assert r.status_code == 400
    # Far-too-short is rejected by request validation (422).
    r2 = admin.post("/api/users", json={"username": "shorty2", "password": "x", "role": "learner"})
    assert r2.status_code == 422
