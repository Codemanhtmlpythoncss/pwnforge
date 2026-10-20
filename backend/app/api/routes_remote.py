"""Remote access: overview, the jump host, Tailscale, and Pwnforge's OpenVPN server and client profiles.

  GET  /api/remote/overview                 private addresses of this host, your labs, what's set up
  GET  /api/remote/setup                    administrators: jump-host, Tailscale and OpenVPN setup commands
  GET  /api/vpn                             VPN status (your profiles; administrators: everyone's)
  POST /api/vpn/init                        administrators: create the VPN certificate authority
  GET  /api/vpn/server-config               administrators: the server configuration and install commands
  POST /api/vpn/clients                     administrators: issue a profile for a user {"user_id", "name"}
  GET  /api/vpn/clients/{id}/profile        the owner (or an administrator) downloads it, once
  POST /api/vpn/clients/{id}/revoke         the owner or an administrator revokes it

Connection details for one lab instance are in the public API: GET /api/v1/lab-instances/{id}/access.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import client_ip, current_user, get_db, require_admin, session_only
from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings
from backend.app.database.models import LabInstance, User, VMStatus
from backend.app.remote import access, openvpn
from backend.app.security import audit

router = APIRouter(prefix="/api", tags=["remote access"])
ID = r"^[0-9a-f]{32}$"


@router.get("/remote/overview", summary="How to reach your lab machines from elsewhere")
def overview(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ts = access.tailscale_status()
    labs = db.execute(select(LabInstance).where(LabInstance.owner_id == user.id, LabInstance.status != VMStatus.deleted)
                      .order_by(LabInstance.created_at.desc())).scalars()
    return {
        "host_addresses": access.host_addresses(db), "jump_user": cfg.get_setting(db, "remote.jump_user") or "pwnforge-jump",
        "ssh_port": int(cfg.get_setting(db, "remote.ssh_port") or 22), "lab_supernet": cfg.get_setting(db, "network.base_cidr"),
        "web_port": int(cfg.get_setting(db, "server.port") or 8080),
        "web_lan_access": bool(cfg.get_setting(db, "server.lan_access")),
        "tailscale": {k: ts[k] for k in ("installed", "running", "ips", "dns_name")},
        "vpn": {"initialised": openvpn.initialised(), "enabled": bool(cfg.get_setting(db, "vpn.enabled"))},
        "your_labs": [{"id": li.id, "lab_id": li.lab_id, "status": li.status.value} for li in labs],
    }


@router.get("/remote/setup", summary="Administrators: the commands to set up remote access on this host")
def setup(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    supernet = cfg.get_setting(db, "network.base_cidr") or "10.200.0.0/16"
    ts = access.tailscale_status(max_age=5)
    return {
        "jump_host": access.jump_host_setup(db),
        "tailscale": {
            "status": ts,
            "install": ["curl -fsSL https://tailscale.com/install.sh | sh   # or your distribution's package",
                        "sudo tailscale up", "tailscale ip -4   # this host's tailnet address"],
            "acl_example": {"grants": [{"src": ["group:pwnforge-learners"], "dst": ["tag:pwnforge-host"], "ip": ["tcp:22", "tcp:%d" % int(cfg.get_setting(db, "server.port") or 8080)]}],
                            "tagOwners": {"tag:pwnforge-host": ["autogroup:admin"]},
                            "groups": {"group:pwnforge-learners": ["learner@example.com"]}},
            "tag_host": "sudo tailscale up --advertise-tags=tag:pwnforge-host",
            "subnet_router_note": ("A subnet router (tailscale up --advertise-routes=%s) only helps for networks this host forwards to. "
                                   "Pwnforge's lab networks are isolated and are not forwarded, so reach lab machines through the "
                                   "jump host instead of advertising them." % supernet),
        },
        "openvpn": openvpn.install_commands(get_settings().data_dir, db),
    }


@router.get("/vpn", summary="VPN status and profiles")
def vpn_status(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return openvpn.status(db, user)


def _vpn(fn):
    try:
        return fn()
    except openvpn.VpnError as e:
        raise HTTPException(e.code, str(e))


@router.post("/vpn/init", summary="Administrators: create the VPN certificate authority")
def vpn_init(request: Request, user: User = Depends(require_admin), _s: User = Depends(session_only), db: Session = Depends(get_db)) -> dict:
    out = _vpn(lambda: openvpn.init_pki(db))
    audit.record(db, action="vpn.init", actor_id=user.id, ip=client_ip(request))
    return out


@router.get("/vpn/server-config", summary="Administrators: the OpenVPN server configuration and how to install it")
def vpn_server_config(user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    if not openvpn.initialised():
        raise HTTPException(409, "Set up the VPN certificate authority first.")
    text = _vpn(lambda: openvpn.write_server_config(db))
    return {"config": text, "path": str(openvpn.vpn_dir() / "server.conf"), "commands": openvpn.install_commands(get_settings().data_dir, db)}


class IssueRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=32, examples=["laptop"])


@router.post("/vpn/clients", summary="Administrators: issue a VPN profile for a user")
def vpn_issue(body: IssueRequest, request: Request, user: User = Depends(require_admin), _s: User = Depends(session_only),
              db: Session = Depends(get_db)) -> dict:
    owner = db.get(User, body.user_id)
    if owner is None:
        raise HTTPException(404, "No such user.")
    row = _vpn(lambda: openvpn.issue(db, owner=owner, name=body.name, actor=user))
    audit.record(db, action="vpn.issue", actor_id=user.id, target_type="vpn_client", target_id=row.id,
                 detail={"for_user": owner.id, "name": body.name}, ip=client_ip(request))
    return openvpn.client_view(row)


@router.get("/vpn/clients/{client_id}/profile", summary="Download a VPN profile (once)")
def vpn_profile(request: Request, client_id: str = Path(..., pattern=ID), user: User = Depends(session_only),
                db: Session = Depends(get_db)) -> Response:
    filename, data = _vpn(lambda: openvpn.take_profile(db, client_id, user))
    audit.record(db, action="vpn.download", actor_id=user.id, target_type="vpn_client", target_id=client_id, ip=client_ip(request))
    db.commit()
    return Response(data, media_type="application/x-openvpn-profile",
                    headers={"Content-Disposition": 'attachment; filename="%s"' % filename, "Cache-Control": "no-store"})


@router.post("/vpn/clients/{client_id}/revoke", summary="Revoke a VPN profile")
def vpn_revoke(request: Request, client_id: str = Path(..., pattern=ID), user: User = Depends(session_only),
               db: Session = Depends(get_db)) -> dict:
    row = _vpn(lambda: openvpn.revoke(db, client_id, user))
    audit.record(db, action="vpn.revoke", actor_id=user.id, target_type="vpn_client", target_id=client_id, ip=client_ip(request))
    return openvpn.client_view(row)
