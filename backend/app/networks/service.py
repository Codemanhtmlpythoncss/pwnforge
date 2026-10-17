"""Virtual network management.

Allocates isolated per-lab subnets from the configured supernet and creates
real networks via the active driver. Isolated is the default; external/NAT
requires both the global ``network.allow_external`` setting and an explicit
per-lab request.
"""
from __future__ import annotations

import ipaddress

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.database.models import NetworkMode, VirtualNetwork
from backend.app.vms.factory import get_driver


class NetworkError(Exception):
    pass


def _allocate_cidr(session: Session) -> str:
    base = cfg.get_setting(session, "network.base_cidr")
    supernet = ipaddress.ip_network(base, strict=False)
    used = {
        n.cidr for n in session.execute(
            select(VirtualNetwork).where(VirtualNetwork.cidr.is_not(None))
        ).scalars()
    }
    for subnet in supernet.subnets(new_prefix=24):
        if str(subnet) not in used:
            return str(subnet)
    raise NetworkError("No free /24 subnet available in the configured supernet.")


def create_network(
    session: Session, *, name: str, mode: str = "isolated",
    external: bool = False, owner_id: int | None = None,
    lab_instance_id: str | None = None,
) -> VirtualNetwork:
    allow_external = bool(cfg.get_setting(session, "network.allow_external"))
    if external and not allow_external:
        raise NetworkError(
            "External connectivity is disabled globally. Enable "
            "network.allow_external first (and confirm the security warning)."
        )
    if external and mode == "isolated":
        mode = "nat"
    cidr = _allocate_cidr(session)
    driver = get_driver()
    ref = driver.create_network(name, cidr, mode, external and allow_external)
    net = VirtualNetwork(
        name=name, mode=NetworkMode(mode), cidr=cidr, driver_ref=ref,
        lab_instance_id=lab_instance_id, owner_id=owner_id,
        external_access=external and allow_external,
    )
    session.add(net)
    session.flush()
    return net


def delete_network(session: Session, net: VirtualNetwork) -> None:
    driver = get_driver()
    if net.driver_ref:
        try:
            driver.delete_network(net.driver_ref)
        except Exception:  # noqa: BLE001 - best-effort teardown
            pass
    session.delete(net)
    session.flush()


def topology(session: Session, lab_instance_id: str) -> dict:
    nets = list(session.execute(
        select(VirtualNetwork).where(VirtualNetwork.lab_instance_id == lab_instance_id)
    ).scalars())
    return {
        "networks": [
            {"id": n.id, "name": n.name, "cidr": n.cidr, "mode": n.mode.value,
             "external": n.external_access}
            for n in nets
        ]
    }
