"""Remote access to authorised lab machines: how to reach them, without opening anything to the internet.

Lab networks are isolated (libvirt networks without forwarding): a lab machine can reach the Pwnforge host's bridge
address and the host can reach it, but nothing is routed in from other networks. So remote access works in two steps:

  1. reach the Pwnforge host privately: over Pwnforge's OpenVPN server, over Tailscale, or on the LAN;
  2. reach the lab machine through the host: the browser console (nothing to install), or SSH with the host as a
     jump host (``ssh -J``) and SSH port forwarding for RDP, web pages and other ports.

The jump account (setting ``remote.jump_user``, default ``pwnforge-jump``) is a no-shell account allowed only to
forward to the lab networks; the setup commands are on the Remote access page and in docs/REMOTE_ACCESS.md.
Passwords for lab machines are part of the exercises and are never shown here.
"""
from __future__ import annotations

import ipaddress
import json
import shutil
import subprocess
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.database.models import LabInstance, VirtualNetwork, VMInstance, VMProfile, VMStatus

# service names used by the machine catalogue -> (what it is, TCP port, how you use it)
SERVICES = {
    "ssh": ("SSH", 22, "ssh"), "sshd": ("SSH", 22, "ssh"),
    "nginx": ("Web server (HTTP)", 80, "web"), "apache2": ("Web server (HTTP)", 80, "web"),
    "app-node": ("Web app (HTTP)", 3000, "web"), "tomcat10": ("Tomcat (HTTP)", 8080, "web"),
    "postgresql": ("PostgreSQL", 5432, "tcp"), "mariadb": ("MariaDB / MySQL", 3306, "tcp"),
    "smbd": ("SMB file shares", 445, "tcp"), "lanmanserver": ("SMB file shares", 445, "tcp"),
}
_TS_CACHE: dict = {"at": 0.0, "data": None}


def tailscale_status(max_age: int = 30) -> dict:
    """This host's Tailscale state, read with `tailscale status --json` (cached). Never raises."""
    now = time.time()
    if _TS_CACHE["data"] is not None and now - _TS_CACHE["at"] < max_age:
        return _TS_CACHE["data"]
    out = {"installed": bool(shutil.which("tailscale")), "running": False, "ips": [], "dns_name": "", "tailnet": "", "error": ""}
    if out["installed"]:
        try:
            r = subprocess.run(["tailscale", "status", "--json", "--peers=false"], capture_output=True, text=True, timeout=4, check=False)
            if r.returncode == 0:
                j = json.loads(r.stdout or "{}")
                me = j.get("Self") or {}
                out.update(running=j.get("BackendState") == "Running", ips=[ip for ip in me.get("TailscaleIPs") or [] if ":" not in ip][:2],
                           dns_name=(me.get("DNSName") or "").rstrip("."), tailnet=(j.get("CurrentTailnet") or {}).get("Name", ""))
            else:
                out["error"] = (r.stderr or r.stdout or "").strip()[:200]
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            out["error"] = str(e)[:200]
    _TS_CACHE.update(at=now, data=out)
    return out


def host_addresses(db: Session) -> list[dict]:
    """Ways clients can reach this host privately, best first."""
    out = []
    configured = (cfg.get_setting(db, "remote.host_address") or "").strip()
    if configured:
        out.append({"address": configured, "via": "configured", "note": "set in Settings (remote.host_address)"})
    ts = tailscale_status()
    if ts["running"]:
        if ts["dns_name"]:
            out.append({"address": ts["dns_name"], "via": "tailscale", "note": "Tailscale MagicDNS name"})
        for ip in ts["ips"]:
            out.append({"address": ip, "via": "tailscale", "note": "Tailscale IP"})
    vpn = (cfg.get_setting(db, "vpn.subnet") or "").strip()
    try:
        if vpn and bool(cfg.get_setting(db, "vpn.enabled")):
            out.append({"address": str(next(ipaddress.ip_network(vpn, strict=False).hosts())), "via": "openvpn",
                        "note": "this host's address inside the OpenVPN tunnel"})
    except ValueError:
        pass
    return out


def _services(profile: VMProfile | None) -> list[dict]:
    seen, out = set(), []
    for name in (profile.services if profile else []) or []:
        if name in SERVICES and SERVICES[name][1] not in seen:
            label, port, kind = SERVICES[name]
            seen.add(port)
            out.append({"service": name, "label": label, "port": port, "kind": kind})
    if profile is not None and profile.os_family == "windows" and 3389 not in seen:
        out.append({"service": "rdp", "label": "Remote Desktop (if enabled on this machine)", "port": 3389, "kind": "rdp"})
    return out


def _how(kind: str, port: int, ip: str, host: str, jump: str, ssh_port: int) -> dict:
    j = "%s@%s" % (jump, host) + ("" if ssh_port == 22 else ":%d" % ssh_port)
    local = {"ssh": 0, "rdp": 13389, "web": 8080 if port != 8080 else 18080}.get(kind, 10000 + port)
    if kind == "ssh":
        return {"steps": ["Connect through the Pwnforge host (it never puts the machine on the internet):"],
                "commands": ["ssh -J %s <lab-user>@%s" % (j, ip)]}
    tunnel = "ssh -N -L %d:%s:%d %s" % (local, ip, port, j)
    if kind == "rdp":
        return {"steps": ["Open a tunnel through the Pwnforge host and leave it running:", "Then point your Remote Desktop client at localhost:%d." % local],
                "commands": [tunnel, "mstsc /v:localhost:%d   (Windows)   ·   xfreerdp /v:localhost:%d   (Linux)" % (local, local)]}
    if kind == "web":
        return {"steps": ["Open a tunnel through the Pwnforge host and leave it running:", "Then browse to http://localhost:%d/." % local],
                "commands": [tunnel]}
    return {"steps": ["Open a tunnel through the Pwnforge host, then connect your client to localhost:%d:" % local], "commands": [tunnel]}


def connection_details(db: Session, li: LabInstance) -> dict:
    hosts = host_addresses(db)
    host = hosts[0]["address"] if hosts else "<pwnforge-host>"
    jump = (cfg.get_setting(db, "remote.jump_user") or "pwnforge-jump").strip()
    ssh_port = int(cfg.get_setting(db, "remote.ssh_port") or 22)
    nets = {n.id: n for n in db.execute(select(VirtualNetwork).where(VirtualNetwork.lab_instance_id == li.id)).scalars()}
    machines = []
    for vm in db.execute(select(VMInstance).where(VMInstance.lab_instance_id == li.id)).scalars():
        prof = db.get(VMProfile, vm.profile_id) if vm.profile_id else None
        net = nets.get(vm.network_id) if vm.network_id else None
        running = vm.status == VMStatus.running
        svcs = []
        for s in _services(prof):
            how = _how(s["kind"], s["port"], vm.ip_address, host, jump, ssh_port) if running and vm.ip_address and vm.driver != "simulation" else None
            svcs.append(dict(s, how=how))
        machines.append({
            "id": vm.id, "name": vm.name, "status": vm.status.value, "ip_address": vm.ip_address,
            "os_family": prof.os_family if prof else None, "simulated": vm.driver == "simulation",
            "network": {"cidr": net.cidr, "mode": net.mode.value, "external_access": net.external_access} if net else None,
            "console": {"path": "/labs/instance/%s" % li.id, "available": running}, "services": svcs,
        })
    notes = ["Lab networks are isolated: reach a machine through the Pwnforge host (SSH jump host or the browser console), "
             "after connecting to the host over your VPN, your tailnet or the LAN. Nothing here is published to the internet.",
             "Lab passwords and keys are part of the exercises, so they aren't shown here."]
    if not hosts:
        notes.append("This host's private address isn't known yet: set remote.host_address in Settings, or set up OpenVPN or Tailscale.")
    if any(m["simulated"] for m in machines):
        notes.append("Some machines are simulated (no real VM on this host), so there is nothing to connect to.")
    return {"lab_instance_id": li.id, "status": li.status.value, "host": host, "host_addresses": hosts, "jump_user": jump,
            "ssh_port": ssh_port, "machines": machines, "notes": notes}


def jump_host_setup(db: Session) -> dict:
    """The one-time commands an administrator runs (as root) to create the restricted jump account."""
    jump = (cfg.get_setting(db, "remote.jump_user") or "pwnforge-jump").strip()
    supernet = cfg.get_setting(db, "network.base_cidr") or "10.200.0.0/16"
    return {
        "jump_user": jump, "lab_supernet": supernet,
        "commands": [
            "sudo useradd --system --create-home --shell /usr/sbin/nologin %s" % jump,
            "sudo install -d -m 0700 -o %s -g %s /home/%s/.ssh" % (jump, jump, jump),
            "# add each authorised person's public key (one per line):",
            "sudo tee -a /home/%s/.ssh/authorized_keys < their_key.pub" % jump,
            "sudo chown %s:%s /home/%s/.ssh/authorized_keys && sudo chmod 0600 /home/%s/.ssh/authorized_keys" % (jump, jump, jump, jump),
        ],
        "sshd_config": ("# /etc/ssh/sshd_config.d/60-pwnforge-jump.conf\nMatch User %s\n    PasswordAuthentication no\n    PermitTTY no\n"
                        "    ForceCommand /usr/sbin/nologin\n    AllowTcpForwarding local\n    X11Forwarding no\n    AllowAgentForwarding no\n"
                        "    PermitTunnel no\n    GatewayPorts no\n" % jump),
        "firewall": ("# Let the jump account reach only the lab networks (nftables):\n"
                     "sudo nft add table inet pwnforge_jump\n"
                     "sudo nft add chain inet pwnforge_jump out '{ type filter hook output priority 0; }'\n"
                     "sudo nft add rule inet pwnforge_jump out meta skuid %s ip daddr != %s drop" % (jump, supernet)),
        "reload": "sudo sshd -t && sudo systemctl reload ssh",
    }
