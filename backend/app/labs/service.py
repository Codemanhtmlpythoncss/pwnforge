"""Multi-machine lab orchestration.

Starts a lab's machines in dependency order on an isolated network, reporting
progress. On partial failure it tears down only the resources created for that
failed lab instance — never unrelated machines or networks.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import (
    Lab, LabInstance, VMInstance, VMStatus, VirtualNetwork,
)
from backend.app.networks import service as networks
from backend.app.security import audit
from backend.app.vms import service as vms


class LabServiceError(Exception):
    pass


def create_lab_instance(session: Session, *, lab_id: str, owner_id: int) -> LabInstance:
    lab = session.get(Lab, lab_id)
    if lab is None:
        raise LabServiceError(f"Unknown lab {lab_id}")
    li = LabInstance(lab_id=lab_id, owner_id=owner_id, status=VMStatus.defined)
    session.add(li)
    session.flush()
    return li


def start_lab(session: Session, li: LabInstance, progress=None) -> LabInstance:
    lab = session.get(Lab, li.lab_id)
    if lab is None:
        raise LabServiceError("lab definition missing")
    created_nets: list[str] = []
    created_vms: list[str] = []
    li.status = VMStatus.starting
    li.last_error = None
    session.flush()

    def report(pct: int, stage: str, detail: str = "") -> None:
        if progress:
            progress.update(percent=pct, stage=stage, detail=detail)

    try:
        # 1. create the lab's networks
        net_refs: dict[str, VirtualNetwork] = {}
        total = max(1, len(lab.networks))
        for i, netdef in enumerate(lab.networks or [{"name": "lab", "mode": "isolated"}]):
            report(int(10 + i / total * 20), f"Creating network {netdef['name']}")
            net = networks.create_network(
                session, name=f"{li.id[:8]}-{netdef['name']}",
                mode=netdef.get("mode", "isolated"),
                external=netdef.get("external", False),
                owner_id=li.owner_id, lab_instance_id=li.id)
            net_refs[netdef["name"]] = net
            created_nets.append(net.id)
        li.network_ids = created_nets

        # 2. determine startup order
        order = lab.startup_order or [m["role"] for m in lab.machines]
        machines_by_role = {m["role"]: m for m in lab.machines}

        # 3. start machines in order
        for i, role in enumerate(order):
            m = machines_by_role.get(role)
            if not m:
                continue
            report(int(30 + (i + 1) / max(1, len(order)) * 60),
                   f"Starting {role} ({m['profile_id']})")
            inst = vms.create_instance(
                session, profile_id=m["profile_id"], owner_id=li.owner_id,
                name=f"{li.id[:8]}-{role}", lab_instance_id=li.id)
            # Track for teardown immediately, so a failure mid-start still cleans up.
            created_vms.append(inst.id)
            # attach to the lab's first/default network (or role-specified)
            net_name = m.get("network") or (lab.networks[0]["name"] if lab.networks else "lab")
            if net_name in net_refs:
                inst.network_id = net_refs[net_name].driver_ref
            session.flush()
            vms.start_instance(session, inst, progress=None)

        li.status = VMStatus.running
        li.started_at = datetime.now(timezone.utc)
        session.flush()
        report(100, "Lab ready")
        audit.record(session, action="lab.start", actor_id=li.owner_id,
                     target_type="lab", target_id=li.id, detail={"lab": lab.id})
        return li
    except Exception as exc:  # noqa: BLE001
        li.status = VMStatus.error
        li.last_error = str(exc)
        session.flush()
        _teardown(session, created_vms, created_nets)
        raise


def stop_lab(session: Session, li: LabInstance) -> LabInstance:
    insts = list(session.execute(
        select(VMInstance).where(VMInstance.lab_instance_id == li.id)).scalars())
    for inst in insts:
        try:
            vms.stop_instance(session, inst, force=True)
        except Exception:  # noqa: BLE001
            continue
    li.status = VMStatus.stopped
    session.flush()
    audit.record(session, action="lab.stop", actor_id=li.owner_id,
                 target_type="lab", target_id=li.id)
    return li


def delete_lab_instance(session: Session, li: LabInstance) -> None:
    vm_ids = [i.id for i in session.execute(
        select(VMInstance).where(VMInstance.lab_instance_id == li.id)).scalars()]
    net_ids = list(li.network_ids or [])
    _teardown(session, vm_ids, net_ids)
    session.delete(li)
    session.flush()


def _teardown(session: Session, vm_ids: list[str], net_ids: list[str]) -> None:
    """Remove ONLY the given VMs/networks (scoped to a single lab instance)."""
    for vid in vm_ids:
        inst = session.get(VMInstance, vid)
        if inst is not None:
            try:
                vms.delete_instance(session, inst)
            except Exception:  # noqa: BLE001
                continue
    for nid in net_ids:
        net = session.get(VirtualNetwork, nid)
        if net is not None:
            try:
                networks.delete_network(session, net)
            except Exception:  # noqa: BLE001
                continue
