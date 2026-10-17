"""Shared test helpers."""
from __future__ import annotations

import time


def poll_job(client, job_id, n=200):
    for _ in range(n):
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("succeeded", "failed"):
            return j
        time.sleep(0.05)
    return client.get(f"/api/jobs/{job_id}").json()


def easy_profile(client):
    return client.get("/api/profiles?difficulty=easy&limit=1").json()["items"][0]["id"]
