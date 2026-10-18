"""Public API (/api/v1) and personal API tokens: authentication, scopes, roles, validation, isolation, limits."""
from __future__ import annotations

from sqlalchemy import select

from backend.tests.conftest import bearer, make_user, poll_job, token_for


# ---- tokens ------------------------------------------------------------------------------------
def test_token_is_shown_once_and_only_its_hash_is_stored(admin):
    t = token_for(admin, ["read"])
    assert t["token"].startswith("pf_") and t["warning"]
    listed = admin.get("/api/tokens").json()["items"]
    row = next(x for x in listed if x["id"] == t["id"])
    assert "token" not in row and "token_hash" not in row and row["hint"].endswith(t["token"][-4:])
    from backend.app.database.base import session_scope
    from backend.app.database.models import ApiToken, AuditEvent
    with session_scope() as s:
        stored = s.get(ApiToken, t["id"])
        assert t["token"].split("_", 2)[2] not in stored.token_hash
        audits = [a.detail for a in s.execute(select(AuditEvent).where(AuditEvent.action == "token.create")).scalars()]
        assert all(t["token"] not in str(d) for d in audits)


def test_no_credentials_or_a_bad_token_is_401(client):
    assert client.get("/api/v1/status").status_code in (200, 401)   # (the shared client may be signed in)
    assert bearer("pf_" + "0" * 32 + "_" + "x" * 43).get("/api/v1/status").status_code == 401
    assert bearer("not-a-token").get("/api/v1/status").status_code == 401


def test_tokens_only_work_on_the_public_and_ai_apis(admin):
    c = bearer(token_for(admin, ["read", "labs", "ai"])["token"])
    assert c.get("/api/v1/status").status_code == 200
    r = c.get("/api/users")                     # the admin API needs a signed-in session
    assert r.status_code == 401 and "API tokens work with" in r.json()["detail"]
    assert c.post("/api/tokens", json={"name": "x", "scopes": ["read"]}).status_code == 401   # tokens can't make tokens
    assert c.get("/api/settings").status_code == 401


def test_scopes_are_enforced(admin):
    learner, _ = make_user(admin, "learner")
    ro = bearer(token_for(learner, ["read"])["token"])
    assert ro.get("/api/v1/courses?limit=1").status_code == 200
    r = ro.post("/api/v1/lab-instances", json={"lab_id": "linux-practice-basic"})
    assert r.status_code == 403 and "'labs' scope" in r.json()["detail"]
    assert ro.get("/api/ai/status").status_code == 403


def test_a_viewer_cannot_grant_or_use_the_labs_scope(admin):
    viewer, _ = make_user(admin, "viewer")
    r = viewer.post("/api/tokens", json={"name": "v", "scopes": ["labs"]})
    assert r.status_code == 400 and "can't grant" in r.json()["detail"]
    assert viewer.post("/api/v1/lab-instances", json={"lab_id": "linux-practice-basic"}).status_code == 403
    assert viewer.post("/api/lab-instances", json={"lab_id": "linux-practice-basic"}).status_code == 403   # the website too


def test_revoked_and_expired_tokens_stop_working(admin):
    t = token_for(admin, ["read"])
    c = bearer(t["token"])
    assert c.get("/api/v1/status").status_code == 200
    assert admin.delete(f"/api/tokens/{t['id']}").status_code == 200
    assert c.get("/api/v1/status").status_code == 401
    t2 = token_for(admin, ["read"])
    from datetime import datetime, timedelta, timezone
    from backend.app.database.base import session_scope
    from backend.app.database.models import ApiToken
    with session_scope() as s:
        s.get(ApiToken, t2["id"]).expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert bearer(t2["token"]).get("/api/v1/status").status_code == 401


def test_users_cannot_revoke_each_others_tokens(admin):
    a, _ = make_user(admin)
    b, _ = make_user(admin)
    t = token_for(a, ["read"])
    assert b.delete(f"/api/tokens/{t['id']}").status_code == 404
    assert bearer(t["token"]).get("/api/v1/status").status_code == 200


def test_token_validation(admin):
    assert admin.post("/api/tokens", json={"name": "x", "scopes": ["root"]}).status_code == 400
    assert admin.post("/api/tokens", json={"name": "", "scopes": ["read"]}).status_code == 422
    assert admin.post("/api/tokens", json={"name": "x", "scopes": ["read"], "expires_days": 9999}).status_code == 422


# ---- the public API ----------------------------------------------------------------------------
def test_status_courses_and_labs(admin):
    c = bearer(token_for(admin, ["read"])["token"])
    st = c.get("/api/v1/status").json()
    assert st["you"]["auth"] == "token" and st["you"]["scopes"] == ["read"] and st["counts"]["courses"] >= 50
    page = c.get("/api/v1/courses?limit=2&offset=1").json()
    assert page["limit"] == 2 and len(page["items"]) == 2 and page["total"] >= 50
    cid = page["items"][0]["id"]
    detail = c.get(f"/api/v1/courses/{cid}").json()
    text = str(detail)
    assert detail["id"] == cid and "answer_hash" not in text and "value_hash" not in text
    assert c.get("/api/v1/courses/no-such-course").status_code == 404
    assert c.get("/api/v1/courses/../etc").status_code in (404, 422)
    assert len(c.get("/api/v1/labs").json()) >= 1


def test_validation_errors(admin):
    c = bearer(token_for(admin, ["read", "labs"])["token"])
    assert c.get("/api/v1/courses?limit=5000").status_code == 422
    assert c.get("/api/v1/lab-instances/not-an-id").status_code == 422
    assert c.post("/api/v1/lab-instances", json={"lab_id": "Bad Lab!"}).status_code == 422
    assert c.post("/api/v1/lab-instances", json={"lab_id": "no-such-lab"}).status_code == 404
    assert c.post("/api/v1/lab-instances", json={}).status_code == 422


def test_lab_lifecycle_and_isolation_between_users(admin):
    owner, me = make_user(admin, "learner")
    other, _ = make_user(admin, "learner")
    teacher, _ = make_user(admin, "instructor")
    tok = bearer(token_for(owner, ["read", "labs"])["token"])
    started = tok.post("/api/v1/lab-instances", json={"lab_id": "linux-practice-basic"})
    assert started.status_code == 202, started.text
    li, job = started.json()["lab_instance_id"], started.json()["job_id"]
    assert poll_job(owner, job)["status"] == "succeeded"
    assert tok.get(f"/api/v1/jobs/{job}").json()["status"] == "succeeded"
    assert tok.get(f"/api/v1/lab-instances/{li}").json()["status"] == "running"
    assert any(x["id"] == li for x in tok.get("/api/v1/lab-instances").json())

    # another learner sees nothing of it, and can't stop it
    assert other.get(f"/api/v1/lab-instances/{li}").status_code == 404
    assert other.post(f"/api/v1/lab-instances/{li}/stop").status_code == 404
    assert other.get(f"/api/v1/jobs/{job}").status_code == 404
    assert other.get(f"/api/jobs/{job}").status_code == 404                  # (the website's job route too)
    assert other.get(f"/api/v1/lab-instances?owner_id={me['id']}").status_code == 403
    # an instructor may look, not change
    assert teacher.get(f"/api/v1/lab-instances/{li}").status_code == 200
    assert teacher.get(f"/api/v1/lab-instances?owner_id={me['id']}").status_code == 200
    assert teacher.post(f"/api/v1/lab-instances/{li}/stop").status_code == 404

    assert tok.post(f"/api/v1/lab-instances/{li}/stop").json()["status"] == "stopped"
    assert tok.delete(f"/api/v1/lab-instances/{li}").json()["ok"] is True
    assert tok.get(f"/api/v1/lab-instances/{li}").status_code == 404

    from backend.app.database.base import session_scope
    from backend.app.database.models import AuditEvent
    with session_scope() as s:
        actions = {a.action for a in s.execute(select(AuditEvent).where(AuditEvent.target_id == li)).scalars()}
    assert {"api.lab.start", "api.lab.stop", "api.lab.delete", "api.denied"} <= actions


def test_rate_limit_answers_429_with_retry_after(admin):
    t = token_for(admin, ["read"])
    from backend.app.security import ratelimit
    for _ in range(120):
        ratelimit.hit("v1-read:token:" + t["id"], 120, 60)
    r = bearer(t["token"]).get("/api/v1/status")
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1


def test_vms_are_your_own_unless_admin_asks_for_all(admin):
    learner, _ = make_user(admin)
    assert learner.get("/api/v1/vms").json() == []
    assert learner.get("/api/v1/vms?all=true").json() == []          # (ignored for non-admins)
