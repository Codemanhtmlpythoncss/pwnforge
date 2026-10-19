"""Multi-machine labs, network isolation, teardown, flags."""
from __future__ import annotations

from backend.tests.helpers import poll_job


def test_multi_machine_lab_starts_isolated(admin):
    ls = admin.post("/api/lab-instances", json={"lab_id": "web-security-lab"}).json()
    j = poll_job(admin, ls["job_id"])
    assert j["status"] == "succeeded", j.get("error")
    li = [x for x in admin.get("/api/lab-instances").json()["items"]
          if x["id"] == ls["lab_instance_id"]][0]
    assert all(m["status"] == "running" for m in li["machines"])
    # distinct IPs on one isolated subnet
    ips = [m["ip_address"] for m in li["machines"]]
    assert len(set(ips)) == len(ips)
    nets = li["topology"]["networks"]
    assert len(nets) == 1 and nets[0]["mode"] == "isolated"
    # cleanup
    admin.post(f"/api/lab-instances/{ls['lab_instance_id']}/stop")
    admin.delete(f"/api/lab-instances/{ls['lab_instance_id']}")


def test_two_labs_get_distinct_subnets(admin):
    a = admin.post("/api/lab-instances", json={"lab_id": "linux-practice-basic"}).json()
    b = admin.post("/api/lab-instances", json={"lab_id": "network-basics-lab"}).json()
    poll_job(admin, a["job_id"]); poll_job(admin, b["job_id"])
    items = admin.get("/api/lab-instances").json()["items"]
    subnets = []
    for li in items:
        for n in li["topology"]["networks"]:
            subnets.append(n["cidr"])
    assert len(set(subnets)) == len(subnets), "each lab must get its own subnet"
    for li in items:
        admin.delete(f"/api/lab-instances/{li['id']}")


def test_flag_submission_server_side(admin):
    from backend.app.vms import provision
    lab = "web-security-lab"
    started = admin.post("/api/lab-instances", json={"lab_id": lab}).json()
    poll_job(admin, started["job_id"])
    li_id = started["lab_instance_id"]
    # The real flag is the one planted in this lab instance (unguessable, re-derived to validate).
    good = admin.post("/api/flags/submit",
                      json={"scope_type": "lab", "scope_id": lab,
                            "value": provision.derive_flag(li_id)}).json()
    assert good["correct"] is True and good["points"] > 0
    # The old guessable PWN{lab_id} and anything else are rejected.
    assert admin.post("/api/flags/submit",
                      json={"scope_type": "lab", "scope_id": lab, "value": f"PWN{{{lab}}}"}).json()["correct"] is False
    bad = admin.post("/api/flags/submit",
                     json={"scope_type": "lab", "scope_id": lab, "value": "nope"}).json()
    assert bad["correct"] is False
    admin.delete(f"/api/lab-instances/{li_id}")


def test_lab_capacity_failure_tears_down(admin):
    # Tiny budget → start fails → no leftover running machines for that instance.
    admin.put("/api/settings/vm.max_total_memory_mb", json={"value": 128})
    ls = admin.post("/api/lab-instances", json={"lab_id": "web-security-lab"}).json()
    j = poll_job(admin, ls["job_id"])
    assert j["status"] == "failed"
    li = [x for x in admin.get("/api/lab-instances").json()["items"]
          if x["id"] == ls["lab_instance_id"]][0]
    # All created machines cleaned up on partial failure.
    assert li["machines"] == []
    admin.put("/api/settings/vm.max_total_memory_mb", json={"value": 32768})
    admin.delete(f"/api/lab-instances/{ls['lab_instance_id']}")
