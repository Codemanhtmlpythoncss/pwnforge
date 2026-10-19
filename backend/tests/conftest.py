"""Pytest fixtures: isolated temp data dir, DB, seeded catalogue, API client.

Tests NEVER touch a real deployment: each run uses a fresh temporary data dir
and its own SQLite database. No real VMs are created — the simulation driver is
used throughout.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _env(tmp_path_factory):
    data = tmp_path_factory.mktemp("pwnforge-test-data")
    os.environ["PWNFORGE_DATA_DIR"] = str(data)
    os.environ["PWNFORGE_DATABASE_URL"] = f"sqlite:///{data/'test.db'}"
    os.environ["PWNFORGE_ENV_FILE"] = str(data / ".env")
    os.environ["PWNFORGE_ENVIRONMENT"] = "test"
    os.environ["PWNFORGE_VM_DRIVER"] = "simulation"
    # Reset cached settings/engine to pick up the test env.
    from backend.app.core.config import get_settings
    from backend.app.database import base as dbbase
    get_settings.cache_clear()
    dbbase._engine = None
    dbbase._SessionFactory = None
    from backend.app.database.init_db import initialise
    initialise(include_profiles=True)
    yield


@pytest.fixture(scope="session")
def client():
    import backend.app.jobs.handlers  # noqa: F401
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    return TestClient(create_app())


@pytest.fixture(scope="session")
def admin(client):
    # Bootstrap the first admin once.
    r = client.post("/api/auth/bootstrap",
                    json={"username": "root", "password": "rootpass12345"})
    if r.status_code == 409:
        client.post("/api/auth/login", json={"username": "root", "password": "rootpass12345"})
    # Raise limits so simulated multi-VM labs fit.
    for k, v in [("vm.max_total_memory_mb", 32768), ("vm.max_concurrent", 20),
                 ("vm.max_total_vcpu", 40)]:
        client.put(f"/api/settings/{k}", json={"value": v})
    return client


@pytest.fixture
def learner(admin):
    """A fresh second client logged in as a learner (for isolation tests)."""
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    import uuid
    uname = f"learner-{uuid.uuid4().hex[:8]}"
    admin.post("/api/users", json={"username": uname, "password": "learnerpass123",
                                   "role": "learner"})
    c = TestClient(create_app())
    c.post("/api/auth/login", json={"username": uname, "password": "learnerpass123"})
    return c


def poll_job(client, job_id, n=200):
    import time
    for _ in range(n):
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("succeeded", "failed"):
            return j
        time.sleep(0.05)
    return client.get(f"/api/jobs/{job_id}").json()


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Each test starts with empty rate-limit windows (many sign-ins happen from one test client)."""
    from backend.app.security import ratelimit
    ratelimit.reset()
    yield


def make_user(admin, role="learner"):
    """A new user of `role` and a client signed in as them: (client, user dict)."""
    import uuid
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    uname = f"{role[:5]}-{uuid.uuid4().hex[:8]}"
    r = admin.post("/api/users", json={"username": uname, "password": "userpass12345", "role": role})
    assert r.status_code == 200, r.text
    c = TestClient(create_app())
    assert c.post("/api/auth/login", json={"username": uname, "password": "userpass12345"}).status_code == 200
    return c, c.get("/api/auth/me").json()["user"]


def token_for(client, scopes, name="test"):
    r = client.post("/api/tokens", json={"name": name, "scopes": scopes, "expires_days": 30})
    assert r.status_code == 201, r.text
    return r.json()


def bearer(token):
    """A cookie-less client that sends only this token."""
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    c = TestClient(create_app())
    c.headers["Authorization"] = "Bearer " + token
    return c
