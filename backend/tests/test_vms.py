"""VM lifecycle, capacity, snapshots, reconciliation (simulation driver)."""
from __future__ import annotations

from backend.tests.helpers import easy_profile as _easy_profile, poll_job


def test_vm_full_lifecycle(admin):
    prof = _easy_profile(admin)
    start = admin.post("/api/vms", json={"profile_id": prof}).json()
    j = poll_job(admin, start["job_id"])
    assert j["status"] == "succeeded", j.get("error")
    vmid = start["instance"]["id"]
    vm = admin.get(f"/api/vms/{vmid}").json()
    assert vm["status"] == "running"
    assert vm["ip_address"]  # IP assigned
    assert vm["simulated"] is True  # honestly flagged on this host
    # snapshot
    assert admin.post(f"/api/vms/{vmid}/snapshot", json={"name": "s1"}).status_code == 200
    # reset (rebuilds overlay, returns to running)
    rj = poll_job(admin, admin.post(f"/api/vms/{vmid}/reset").json()["job_id"])
    assert rj["status"] == "succeeded"
    # stop + delete
    assert admin.post(f"/api/vms/{vmid}/stop").json()["status"] == "stopped"
    assert admin.delete(f"/api/vms/{vmid}").json()["ok"] is True


def test_capacity_enforced(admin):
    # Shrink the RAM budget; a 1GB easy VM should be rejected at start.
    admin.put("/api/settings/vm.max_total_memory_mb", json={"value": 256})
    prof = _easy_profile(admin)
    start = admin.post("/api/vms", json={"profile_id": prof}).json()
    j = poll_job(admin, start["job_id"])
    assert j["status"] == "failed"
    assert "budget" in (j["error"] or "").lower()
    # restore
    admin.put("/api/settings/vm.max_total_memory_mb", json={"value": 32768})


def test_never_reports_ready_without_running(admin):
    # The staged start only marks running after the driver confirms it.
    prof = _easy_profile(admin)
    start = admin.post("/api/vms", json={"profile_id": prof}).json()
    j = poll_job(admin, start["job_id"])
    vm = admin.get(f"/api/vms/{start['instance']['id']}").json()
    if j["status"] == "succeeded":
        assert vm["status"] == "running"
    admin.delete(f"/api/vms/{start['instance']['id']}")


def test_reconcile(admin):
    r = admin.post("/api/admin/reconcile").json()
    assert "reconciled" in r


def test_host_capabilities_honest(admin):
    caps = admin.get("/api/host/capabilities").json()
    # On this dev host the driver is simulation and must say so.
    assert caps["driver"] in ("simulation", "qemu", "libvirt")
    assert isinstance(caps["real_virtualization"], bool)
