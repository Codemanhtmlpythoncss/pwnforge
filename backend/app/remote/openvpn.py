"""OpenVPN server for private remote access to the Pwnforge host (and through it, the lab machines).

Pwnforge keeps its own small certificate authority in ``<data_dir>/vpn`` (directory 0700, private keys 0600):
a CA, the server certificate, a tls-crypt key and a certificate revocation list. It generates the server
configuration and, per authorised person, a client profile (.ovpn) with its own key and certificate.

Security model:
  - the client's private key is created on the server and leaves it exactly once, inside the profile its owner
    downloads; the copy on the server is deleted at that moment (a lost profile is revoked and issued again);
  - revoking a client adds its certificate to the CRL; the server checks the CRL on every connection;
  - the tunnel reaches this host only: no default route and no lab routes are pushed. Lab machines are reached
    through the host (the SSH jump host or the browser console), so the isolated lab networks stay isolated;
  - running the OpenVPN daemon needs root, which Pwnforge never has: an administrator installs the generated
    files with the commands this module prints (and opens the UDP port on the firewall/router only if wanted).
"""
from __future__ import annotations

import ipaddress
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.models import User, UserRole, VpnClient

SERVER_CN = "pwnforge-vpn-server"
ETC = "/etc/openvpn/server/pwnforge"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$|^[0-9a-fA-F:]{2,45}$")


class VpnError(Exception):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message)
        self.code = code


def vpn_dir() -> Path:
    return get_settings().data_dir / "vpn"


def _write(path: Path, data: bytes, mode: int) -> None:
    """Write a file with its permissions set before any data is in it."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def _pem_key(k) -> bytes:
    return k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())


def _pem_cert(c: x509.Certificate) -> bytes:
    return c.public_bytes(serialization.Encoding.PEM)


def _name(cn: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Pwnforge")])


def _cert(subject_cn: str, pub, issuer: x509.Name, signer, days: int, *, ca: bool = False, eku=None) -> x509.Certificate:
    now = datetime.now(timezone.utc)
    b = (x509.CertificateBuilder().subject_name(_name(subject_cn)).issuer_name(issuer).public_key(pub)
         .serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(minutes=5))
         .not_valid_after(now + timedelta(days=days))
         .add_extension(x509.BasicConstraints(ca=ca, path_length=0 if ca else None), critical=True)
         .add_extension(x509.SubjectKeyIdentifier.from_public_key(pub), critical=False))
    if ca:
        b = b.add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True, content_commitment=False,
                                          key_encipherment=False, data_encipherment=False, key_agreement=False,
                                          encipher_only=False, decipher_only=False), critical=True)
    else:
        b = b.add_extension(x509.KeyUsage(digital_signature=True, key_agreement=True, key_cert_sign=False, crl_sign=False,
                                          content_commitment=False, key_encipherment=False, data_encipherment=False,
                                          encipher_only=False, decipher_only=False), critical=True)
        b = b.add_extension(x509.ExtendedKeyUsage([eku]), critical=False)
    return b.sign(signer, hashes.SHA256())


def tls_crypt_key() -> bytes:
    """An OpenVPN static key (2048 bits) in the format openvpn --genkey writes."""
    raw = secrets.token_bytes(256).hex()
    lines = [raw[i:i + 32] for i in range(0, len(raw), 32)]
    return ("#\n# 2048 bit OpenVPN static key (Pwnforge)\n#\n-----BEGIN OpenVPN Static key V1-----\n"
            + "\n".join(lines) + "\n-----END OpenVPN Static key V1-----\n").encode()


def initialised() -> bool:
    d = vpn_dir()
    return all((d / f).exists() for f in ("ca.crt", "ca.key", "server.crt", "server.key", "tls-crypt.key", "crl.pem"))


def init_pki(db: Session) -> dict:
    """Create the CA, server certificate, tls-crypt key and an empty CRL. Refuses to overwrite an existing one."""
    if initialised():
        raise VpnError("The VPN certificate authority already exists.", 409)
    d = vpn_dir()
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(d, 0o700)
    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca = _cert("Pwnforge VPN CA", ca_key.public_key(), _name("Pwnforge VPN CA"), ca_key, 3650, ca=True)
    srv_key = ec.generate_private_key(ec.SECP256R1())
    srv = _cert(SERVER_CN, srv_key.public_key(), ca.subject, ca_key, 825, eku=ExtendedKeyUsageOID.SERVER_AUTH)
    _write(d / "ca.key", _pem_key(ca_key), 0o600)
    _write(d / "ca.crt", _pem_cert(ca), 0o644)
    _write(d / "server.key", _pem_key(srv_key), 0o600)
    _write(d / "server.crt", _pem_cert(srv), 0o644)
    _write(d / "tls-crypt.key", tls_crypt_key(), 0o600)
    _write_crl(db)
    return status(db, None)


def _ca() -> tuple[x509.Certificate, ec.EllipticCurvePrivateKey]:
    d = vpn_dir()
    ca = x509.load_pem_x509_certificate((d / "ca.crt").read_bytes())
    key = serialization.load_pem_private_key((d / "ca.key").read_bytes(), password=None)
    return ca, key


def _write_crl(db: Session) -> None:
    ca, key = _ca()
    now = datetime.now(timezone.utc)
    b = x509.CertificateRevocationListBuilder().issuer_name(ca.subject).last_update(now - timedelta(minutes=5)).next_update(now + timedelta(days=3650))
    for c in db.execute(select(VpnClient).where(VpnClient.revoked_at.is_not(None))).scalars():
        b = b.add_revoked_certificate(x509.RevokedCertificateBuilder().serial_number(int(c.serial, 16))
                                      .revocation_date(c.revoked_at.replace(tzinfo=timezone.utc)).build())
    _write(vpn_dir() / "crl.pem", b.sign(key, hashes.SHA256()).public_bytes(serialization.Encoding.PEM), 0o644)


def _net(db: Session) -> ipaddress.IPv4Network:
    try:
        n = ipaddress.ip_network(cfg.get_setting(db, "vpn.subnet") or "10.8.0.0/24", strict=False)
    except ValueError:
        raise VpnError("vpn.subnet isn't a valid network (e.g. 10.8.0.0/24).")
    if n.version != 4 or n.prefixlen > 29 or not n.is_private:
        raise VpnError("vpn.subnet must be a private IPv4 network of at least /29.")
    lab = ipaddress.ip_network(cfg.get_setting(db, "network.base_cidr") or "10.200.0.0/16", strict=False)
    if n.overlaps(lab):
        raise VpnError("vpn.subnet overlaps the lab networks (%s): pick another range." % lab)
    return n


def _endpoint(db: Session) -> tuple[str, int, str]:
    host = (cfg.get_setting(db, "vpn.public_host") or "").strip()
    port = int(cfg.get_setting(db, "vpn.port") or 1194)
    proto = (cfg.get_setting(db, "vpn.protocol") or "udp").strip().lower()
    if proto not in ("udp", "tcp"):
        raise VpnError("vpn.protocol must be udp or tcp.")
    if not 1 <= port <= 65535:
        raise VpnError("vpn.port must be 1 to 65535.")
    if host and not HOST_RE.match(host):
        raise VpnError("vpn.public_host must be a host name or an IP address.")
    return host, port, proto


def server_config(db: Session) -> str:
    n = _net(db)
    _, port, proto = _endpoint(db)
    return f"""# Pwnforge OpenVPN server (generated by Pwnforge; install it with the commands on the Remote access page).
# Clients reach this host only (its tunnel address is the first one in {n}); lab machines are reached through
# the host's SSH jump host or browser console, so no routes into the isolated lab networks are pushed.
port {port}
proto {proto}
dev tun
topology subnet
server {n.network_address} {n.netmask}
ca {ETC}/ca.crt
cert {ETC}/server.crt
key {ETC}/server.key
dh none
ecdh-curve prime256v1
tls-crypt {ETC}/tls-crypt.key
crl-verify {ETC}/crl.pem
tls-version-min 1.2
remote-cert-tls client
verify-client-cert require
data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305
auth SHA256
keepalive 10 120
persist-key
persist-tun
user nobody
group nogroup
status /run/openvpn-server/status-pwnforge.log
verb 3
"""


def _client_profile(db: Session, cert: bytes, key: bytes) -> bytes:
    host, port, proto = _endpoint(db)
    d = vpn_dir()
    head = f"""# Pwnforge VPN profile. Keep this file private: it contains your key.
client
dev tun
proto {proto}
remote {host or 'YOUR-PWNFORGE-HOST'} {port}
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
verify-x509-name {SERVER_CN} name
auth-nocache
auth SHA256
data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305
verb 3
"""
    return (head + "<ca>\n" + (d / "ca.crt").read_text() + "</ca>\n<cert>\n" + cert.decode() + "</cert>\n<key>\n" + key.decode()
            + "</key>\n<tls-crypt>\n" + (d / "tls-crypt.key").read_text() + "</tls-crypt>\n").encode()


def issue(db: Session, *, owner: User, name: str, actor: User) -> VpnClient:
    if actor.role != UserRole.administrator:
        raise VpnError("Only administrators issue VPN profiles.", 403)
    if not initialised():
        raise VpnError("Set up the VPN certificate authority first.", 409)
    if not NAME_RE.match(name or ""):
        raise VpnError("Name the device: letters, digits, dot, dash or underscore (up to 32).")
    host, _, _ = _endpoint(db)
    if not host:
        raise VpnError("Set vpn.public_host first (the address clients connect to).", 409)
    _net(db)
    if not owner.is_active:
        raise VpnError("That user is disabled.")
    days = int(cfg.get_setting(db, "vpn.client_days") or 365)
    ca, ca_key = _ca()
    key = ec.generate_private_key(ec.SECP256R1())
    cert = _cert("%s-%s" % (owner.username, name), key.public_key(), ca.subject, ca_key, days, eku=ExtendedKeyUsageOID.CLIENT_AUTH)
    row = VpnClient(user_id=owner.id, name=name, serial="%x" % cert.serial_number, created_by=actor.id,
                    expires_at=cert.not_valid_after_utc)
    db.add(row)
    db.flush()
    _write(vpn_dir() / "issued" / ("%s.crt" % row.serial), _pem_cert(cert), 0o644)
    _write(vpn_dir() / "pending" / ("%s.ovpn" % row.id), _client_profile(db, _pem_cert(cert), _pem_key(key)), 0o600)
    return row


def take_profile(db: Session, client_id: str, user: User) -> tuple[str, bytes]:
    """The profile, once, for its owner (or an administrator); the server's copy is then deleted."""
    row = db.get(VpnClient, client_id)
    if row is None or (row.user_id != user.id and user.role != UserRole.administrator):
        raise VpnError("No such VPN profile.", 404)
    if row.revoked_at is not None:
        raise VpnError("That profile was revoked.", 410)
    path = vpn_dir() / "pending" / ("%s.ovpn" % row.id)
    if row.downloaded_at is not None or not path.exists():
        raise VpnError("That profile was already downloaded, and its key isn't kept on the server. Revoke it and issue a new one if it's lost.", 410)
    data = path.read_bytes()
    path.unlink()
    row.downloaded_at = datetime.now(timezone.utc)
    db.flush()
    owner = db.get(User, row.user_id)
    return "pwnforge-%s-%s.ovpn" % (owner.username if owner else "user", row.name), data


def revoke(db: Session, client_id: str, actor: User) -> VpnClient:
    row = db.get(VpnClient, client_id)
    if row is None or (row.user_id != actor.id and actor.role != UserRole.administrator):
        raise VpnError("No such VPN profile.", 404)
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.flush()
        _write_crl(db)
    pending = vpn_dir() / "pending" / ("%s.ovpn" % row.id)
    if pending.exists():
        pending.unlink()
    return row


def client_view(c: VpnClient) -> dict:
    iso = lambda d: d.isoformat() if d else None  # noqa: E731
    return {"id": c.id, "user_id": c.user_id, "name": c.name, "serial": c.serial, "created_at": iso(c.created_at),
            "expires_at": iso(c.expires_at), "downloaded": c.downloaded_at is not None, "downloaded_at": iso(c.downloaded_at),
            "revoked": c.revoked_at is not None, "revoked_at": iso(c.revoked_at)}


def install_commands(data_dir: Path) -> dict:
    src = data_dir / "vpn"
    return {
        "install": [
            "sudo apt install openvpn            # Debian/Ubuntu; other distributions: their openvpn package",
            f"sudo install -d -m 0755 {ETC}",
            f"sudo install -m 0644 {src}/ca.crt {src}/server.crt {src}/crl.pem {ETC}/",
            f"sudo install -m 0600 {src}/server.key {src}/tls-crypt.key {ETC}/",
            f"sudo install -m 0600 {src}/server.conf /etc/openvpn/server/pwnforge.conf",
            "sudo systemctl enable --now openvpn-server@pwnforge",
            "sudo systemctl status openvpn-server@pwnforge --no-pager",
        ],
        "crl_sync": (
            "# Keep the server's revocation list in step with Pwnforge's (run once, as root):\n"
            "sudo tee /etc/systemd/system/pwnforge-vpn-crl.path >/dev/null <<'EOF'\n"
            "[Path]\nPathChanged=%s/crl.pem\n[Install]\nWantedBy=multi-user.target\nEOF\n"
            "sudo tee /etc/systemd/system/pwnforge-vpn-crl.service >/dev/null <<'EOF'\n"
            "[Service]\nType=oneshot\nExecStart=/usr/bin/install -m 0644 %s/crl.pem %s/crl.pem\nEOF\n"
            "sudo systemctl daemon-reload && sudo systemctl enable --now pwnforge-vpn-crl.path" % (src, src, ETC)),
        "firewall": [
            "# Allow the VPN port on this host's firewall (pick the one you use):",
            "sudo ufw allow PORT/PROTO",
            "sudo nft add rule inet filter input PROTO dport PORT accept",
        ],
    }


def status(db: Session, user: User | None) -> dict:
    d = vpn_dir()
    out = {"initialised": initialised(), "settings": {}, "warnings": [], "clients": [], "files": {}}
    try:
        host, port, proto = _endpoint(db)
        out["settings"] = {"public_host": host, "port": port, "protocol": proto, "subnet": str(_net(db)),
                           "enabled": bool(cfg.get_setting(db, "vpn.enabled")), "client_days": int(cfg.get_setting(db, "vpn.client_days") or 365)}
        if not host:
            out["warnings"].append("vpn.public_host isn't set: clients won't know where to connect.")
    except VpnError as e:
        out["warnings"].append(str(e))
    if out["initialised"]:
        srv = x509.load_pem_x509_certificate((d / "server.crt").read_bytes())
        ca = x509.load_pem_x509_certificate((d / "ca.crt").read_bytes())
        out["ca_fingerprint"] = ca.fingerprint(hashes.SHA256()).hex(":")
        out["server_cert_expires"] = srv.not_valid_after_utc.isoformat()
        perms = {f: oct(os.stat(d / f).st_mode & 0o777) for f in ("ca.key", "server.key", "tls-crypt.key")}
        out["files"] = {"dir": str(d), "key_permissions": perms}
        if any(p != "0o600" for p in perms.values()):
            out["warnings"].append("A private key file isn't 0600: run chmod 600 on %s/*.key." % d)
    if user is not None:
        q = select(VpnClient).order_by(VpnClient.created_at.desc())
        if user.role != UserRole.administrator:
            q = q.where(VpnClient.user_id == user.id)
        out["clients"] = [client_view(c) for c in db.execute(q).scalars()]
    return out


def write_server_config(db: Session) -> str:
    text = server_config(db)
    _write(vpn_dir() / "server.conf", text.encode(), 0o600)
    return text
