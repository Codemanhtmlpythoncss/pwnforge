"""Remote access (connection details, jump host, Tailscale), the OpenVPN CA and profiles, and the API docs page."""
from __future__ import annotations

import os
import stat

import pytest
from cryptography import x509

from backend.app.remote import access, openvpn
from backend.tests.conftest import make_user, poll_job


@pytest.fixture
def vpn(admin, tmp_path, monkeypatch):
    """A fresh VPN directory for each test."""
    monkeypatch.setattr(openvpn, "vpn_dir", lambda: tmp_path / "vpn")
    for k, v in [("vpn.public_host", "vpn.example.test"), ("vpn.subnet", "10.8.0.0/24"), ("vpn.port", 1194), ("vpn.protocol", "udp")]:
        admin.put(f"/api/settings/{k}", json={"value": v})
    return tmp_path / "vpn"


def test_overview_and_connection_details(admin):
    owner, _ = make_user(admin)
    other, _ = make_user(admin)
    admin.put("/api/settings/remote.host_address", json={"value": "pwnforge.tailnet-example.ts.net"})
    started = owner.post("/api/lab-instances", json={"lab_id": "linux-practice-basic"}).json()
    assert poll_job(owner, started["job_id"])["status"] == "succeeded"
    li = started["lab_instance_id"]
    ov = owner.get("/api/remote/overview").json()
    assert ov["host_addresses"][0]["address"] == "pwnforge.tailnet-example.ts.net"
    assert any(x["id"] == li for x in ov["your_labs"])
    d = owner.get(f"/api/v1/lab-instances/{li}/access").json()
    assert d["host"] == "pwnforge.tailnet-example.ts.net" and d["jump_user"] == "pwnforge-jump"
    assert d["machines"] and all(m["console"]["path"] == f"/labs/instance/{li}" for m in d["machines"])
    assert any("isolated" in n for n in d["notes"]) and any("simulated" in n for n in d["notes"])
    assert "password" not in str(d["machines"]).lower()
    assert other.get(f"/api/v1/lab-instances/{li}/access").status_code == 404
    admin.put("/api/settings/remote.host_address", json={"value": ""})


def test_commands_go_through_the_jump_host():
    how = access._how("ssh", 22, "10.200.3.10", "host.example", "pwnforge-jump", 22)
    assert how["commands"] == ["ssh -J pwnforge-jump@host.example <lab-user>@10.200.3.10"]
    rdp = access._how("rdp", 3389, "10.200.3.11", "host.example", "pwnforge-jump", 2222)
    assert rdp["commands"][0] == "ssh -N -L 13389:10.200.3.11:3389 pwnforge-jump@host.example:2222"
    web = access._how("web", 80, "10.200.3.12", "host.example", "pwnforge-jump", 22)
    assert "8080:10.200.3.12:80" in web["commands"][0]


def test_setup_is_for_administrators_and_restricts_the_jump_account(admin):
    learner, _ = make_user(admin)
    assert learner.get("/api/remote/setup").status_code == 403
    s = admin.get("/api/remote/setup").json()
    cfg = s["jump_host"]["sshd_config"]
    assert "PermitTTY no" in cfg and "ForceCommand /usr/sbin/nologin" in cfg and "PasswordAuthentication no" in cfg
    assert "meta skuid pwnforge-jump" in s["jump_host"]["firewall"]
    assert "isolated" in s["tailscale"]["subnet_router_note"]
    assert s["tailscale"]["acl_example"]["grants"][0]["dst"] == ["tag:pwnforge-host"]


def test_tailscale_absent_is_reported_not_an_error(monkeypatch):
    monkeypatch.setattr(access.shutil, "which", lambda name: None)
    access._TS_CACHE.update(at=0.0, data=None)
    st = access.tailscale_status()
    assert st["installed"] is False and st["running"] is False
    access._TS_CACHE.update(at=0.0, data=None)


# ---- OpenVPN -----------------------------------------------------------------------------------
def test_only_administrators_set_it_up_and_keys_are_private(admin, vpn):
    learner, _ = make_user(admin)
    assert learner.post("/api/vpn/init").status_code == 403
    r = admin.post("/api/vpn/init")
    assert r.status_code == 200 and r.json()["initialised"] is True
    assert admin.post("/api/vpn/init").status_code == 409            # never overwritten
    assert stat.S_IMODE(os.stat(vpn).st_mode) == 0o700
    for f in ("ca.key", "server.key", "tls-crypt.key"):
        assert stat.S_IMODE(os.stat(vpn / f).st_mode) == 0o600
    assert "BEGIN OpenVPN Static key V1" in (vpn / "tls-crypt.key").read_text()


def test_server_config_reaches_only_this_host(admin, vpn):
    admin.post("/api/vpn/init")
    cfg = admin.get("/api/vpn/server-config").json()["config"]
    for line in ("server 10.8.0.0 255.255.255.0", "crl-verify", "tls-crypt", "remote-cert-tls client", "user nobody"):
        assert line in cfg
    assert "redirect-gateway" not in cfg and "push \"route" not in cfg
    admin.put("/api/settings/vpn.subnet", json={"value": "10.200.5.0/24"})      # overlaps the labs
    assert admin.get("/api/vpn/server-config").status_code == 400
    admin.put("/api/settings/vpn.subnet", json={"value": "10.8.0.0/24"})


def test_profiles_are_issued_downloaded_once_and_revoked(admin, vpn):
    owner, me = make_user(admin)
    other, _ = make_user(admin)
    admin.post("/api/vpn/init")
    assert owner.post("/api/vpn/clients", json={"user_id": me["id"], "name": "laptop"}).status_code == 403
    assert admin.post("/api/vpn/clients", json={"user_id": me["id"], "name": "bad name!"}).status_code == 400
    c = admin.post("/api/vpn/clients", json={"user_id": me["id"], "name": "laptop"}).json()
    assert stat.S_IMODE(os.stat(vpn / "pending" / (c["id"] + ".ovpn")).st_mode) == 0o600
    assert other.get(f"/api/vpn/clients/{c['id']}/profile").status_code == 404
    assert [x["id"] for x in owner.get("/api/vpn").json()["clients"]] == [c["id"]]
    assert other.get("/api/vpn").json()["clients"] == []

    r = owner.get(f"/api/vpn/clients/{c['id']}/profile")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    prof = r.text
    for part in ("remote vpn.example.test 1194", "<ca>", "<cert>", "<key>", "<tls-crypt>", "verify-x509-name pwnforge-vpn-server name"):
        assert part in prof
    assert not (vpn / "pending" / (c["id"] + ".ovpn")).exists()          # the key is gone from the server
    assert owner.get(f"/api/vpn/clients/{c['id']}/profile").status_code == 410

    # the client certificate is signed by the CA and is for clients only
    ca = x509.load_pem_x509_certificate((vpn / "ca.crt").read_bytes())
    cert = x509.load_pem_x509_certificate(prof.split("<cert>\n")[1].split("</cert>")[0].encode())
    cert.verify_directly_issued_by(ca)
    assert x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value

    assert other.post(f"/api/vpn/clients/{c['id']}/revoke").status_code == 404
    assert owner.post(f"/api/vpn/clients/{c['id']}/revoke").json()["revoked"] is True
    crl = x509.load_pem_x509_crl((vpn / "crl.pem").read_bytes())
    assert crl.get_revoked_certificate_by_serial_number(cert.serial_number) is not None
    crl.is_signature_valid(ca.public_key())


def test_issuing_needs_a_public_host(admin, vpn):
    _, me = make_user(admin)
    admin.post("/api/vpn/init")
    admin.put("/api/settings/vpn.public_host", json={"value": ""})
    r = admin.post("/api/vpn/clients", json={"user_id": me["id"], "name": "phone"})
    assert r.status_code == 409 and "vpn.public_host" in r.json()["detail"]


# ---- API docs ----------------------------------------------------------------------------------
def test_docs_use_no_cdn_and_document_the_security(client):
    r = client.get("/api/docs")
    assert r.status_code == 200 and "cdn." not in r.text and "<script>" not in r.text
    assert client.get("/api/docs/init.js").headers["content-type"].startswith("application/javascript")
    spec = client.get("/api/openapi.json").json()
    assert "bearerAuth" in spec["components"]["securitySchemes"]
    assert {"/api/v1/status", "/api/v1/lab-instances", "/api/ai/chat", "/api/tokens"} <= set(spec["paths"])
    assert spec["paths"]["/api/v1/status"]["get"]["security"][0] == {"bearerAuth": []}
