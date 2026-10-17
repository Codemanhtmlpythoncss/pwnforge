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
    data = tmp_path_factory.mktemp("hacklab-test-data")
    os.environ["HACKLAB_DATA_DIR"] = str(data)
    os.environ["HACKLAB_DATABASE_URL"] = f"sqlite:///{data/'test.db'}"
    os.environ["HACKLAB_ENV_FILE"] = str(data / ".env")
    os.environ["HACKLAB_VM_DRIVER"] = "simulation"
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
