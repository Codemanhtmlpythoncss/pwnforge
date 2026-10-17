"""VM capacity planner.

Decides whether a VM may start given configured limits, currently-committed
reservations and real host memory. Enforces the admin-configurable RAM ceiling
(``vm.max_total_memory_mb``), per-user budgets, concurrency and host headroom.
"""
from __future__ import annotations

from dataclasses import dataclass

import psutil
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.database.models import ResourceReservation, VMInstance, VMStatus


@dataclass
class CapacityDecision:
    allowed: bool
    reason: str = ""
    committed_memory_mb: int = 0
    committed_vcpu: int = 0
    running_count: int = 0


def _committed(session: Session) -> tuple[int, int, int]:
    rows = session.execute(
        select(
            func.coalesce(func.sum(ResourceReservation.memory_mb), 0),
            func.coalesce(func.sum(ResourceReservation.vcpu), 0),
            func.count(),
        ).where(ResourceReservation.active.is_(True))
    ).one()
    return int(rows[0]), int(rows[1]), int(rows[2])


def can_start(session: Session, *, vcpu: int, memory_mb: int, owner_id: int) -> CapacityDecision:
    mem_committed, vcpu_committed, running = _committed(session)

    max_mem = int(cfg.get_setting(session, "vm.max_total_memory_mb"))
    max_vcpu = int(cfg.get_setting(session, "vm.max_total_vcpu"))
    max_conc = int(cfg.get_setting(session, "vm.max_concurrent"))
    overcommit = float(cfg.get_setting(session, "vm.ram_overcommit_ratio"))
    reserve_host = int(cfg.get_setting(session, "vm.reserve_host_memory_mb"))
    per_user = int(cfg.get_setting(session, "vm.per_user_memory_mb"))

    d = CapacityDecision(
        allowed=True, committed_memory_mb=mem_committed,
        committed_vcpu=vcpu_committed, running_count=running,
    )

    if running + 1 > max_conc:
        return CapacityDecision(False, f"Concurrent VM limit reached ({max_conc}).",
                                mem_committed, vcpu_committed, running)
    if mem_committed + memory_mb > int(max_mem * overcommit):
        return CapacityDecision(
            False,
            f"RAM budget exceeded: {mem_committed}+{memory_mb}MB > "
            f"{int(max_mem * overcommit)}MB (limit {max_mem}MB x{overcommit}).",
            mem_committed, vcpu_committed, running)
    if vcpu_committed + vcpu > max_vcpu:
        return CapacityDecision(False, f"vCPU budget exceeded (limit {max_vcpu}).",
                                mem_committed, vcpu_committed, running)

    # Real host headroom check (never silently overcommit beyond physical RAM).
    # Simulated VMs consume no real memory, so this physical check applies only
    # to drivers that actually boot guests.
    from backend.app.vms.factory import active_capabilities
    if active_capabilities().real_virtualization:
        avail_mb = int(psutil.virtual_memory().available / 1024 / 1024)
        if memory_mb > max(0, avail_mb - reserve_host):
            return CapacityDecision(
                False,
                f"Insufficient host RAM: need {memory_mb}MB, "
                f"{avail_mb}MB available minus {reserve_host}MB host reserve.",
                mem_committed, vcpu_committed, running)

    # Optional per-user budget.
    if per_user > 0:
        user_mem = int(session.execute(
            select(func.coalesce(func.sum(ResourceReservation.memory_mb), 0))
            .where(ResourceReservation.active.is_(True),
                   ResourceReservation.owner_id == owner_id)
        ).scalar_one())
        if user_mem + memory_mb > per_user:
            return CapacityDecision(
                False, f"Per-user RAM budget exceeded ({per_user}MB).",
                mem_committed, vcpu_committed, running)

    return d
