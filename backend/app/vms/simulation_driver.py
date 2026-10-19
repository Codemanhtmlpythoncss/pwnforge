"""Simulation driver.

A deterministic, honest stand-in for hosts without a hypervisor. It does NOT
boot real operating systems and never claims to. State is persisted to a JSON
file in the data dir so that reconciliation across process restarts behaves
like a real backend. The orchestration layer flags every instance created on
this driver as ``driver="simulation"`` and the UI shows a clear banner.

Use it only in isolated automated tests. Production and development launches
require a real VM backend or fail with an actionable setup message.
"""
from __future__ import annotations

import ipaddress
import json
import platform
import threading
from pathlib import Path

import psutil

from backend.app.core.config import get_settings
from backend.app.database.models import VMStatus
from backend.app.vms.driver import (
    ConsoleInfo,
    DriverError,
    HostCapabilities,
    VMDriver,
    VMSpec,
)


class SimulationDriver(VMDriver):
    name = "simulation"

    def __init__(self, state_path: Path | None = None) -> None:
        self._lock = threading.RLock()
        self._state_path = state_path or (get_settings().data_dir / "simulation_state.json")
        self._state: dict = self._load()

    # -- persistence --------------------------------------------------------
    def _load(self) -> dict:
        try:
            if self._state_path.exists():
                return json.loads(self._state_path.read_text())
        except (OSError, json.JSONDecodeError):
            pass
        return {"domains": {}, "networks": {}, "overlays": {}, "ip_counter": 10, "vnc_counter": 5900}

    def _save(self) -> None:
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(json.dumps(self._state, indent=2))
        except OSError:
            pass

    # -- capabilities -------------------------------------------------------
    def capabilities(self) -> HostCapabilities:
        return HostCapabilities(
            driver=self.name,
            platform=platform.system().lower(),
            arch=platform.machine(),
            cpu_count=psutil.cpu_count(logical=True) or 1,
            total_memory_mb=int(psutil.virtual_memory().total / (1024 * 1024)),
            real_virtualization=False,
            hardware_acceleration=False,
            features={
                "snapshots": True, "clone": True, "pause": True,
                "console": True, "networks": True, "copy_on_write": True,
            },
            notes=[
                "Simulation driver: VMs are modelled, not booted.",
                "No guest operating system runs; terminals/consoles are simulated.",
                "Switch to the libvirt driver on a Debian/KVM host for real VMs.",
            ],
        )

    # -- overlays -----------------------------------------------------------
    def create_overlay(self, base_image_path: str, overlay_path: str, size_gb: int) -> None:
        with self._lock:
            self._state["overlays"][overlay_path] = {
                "base": base_image_path, "size_gb": size_gb,
            }
            self._save()

    def delete_overlay(self, overlay_path: str) -> None:
        with self._lock:
            self._state["overlays"].pop(overlay_path, None)
            self._save()

    # -- networks -----------------------------------------------------------
    def create_network(self, name: str, cidr: str, mode: str, external: bool) -> str:
        with self._lock:
            ref = f"simnet-{name}"
            self._state["networks"][ref] = {
                "name": name, "cidr": cidr, "mode": mode, "external": external,
            }
            self._save()
            return ref

    def delete_network(self, ref: str) -> None:
        with self._lock:
            self._state["networks"].pop(ref, None)
            self._save()

    # -- domains ------------------------------------------------------------
    def define(self, spec: VMSpec) -> str:
        with self._lock:
            ref = f"simdom-{spec.name}"
            self._state["ip_counter"] += 1
            self._state["vnc_counter"] += 1
            net = self._state["networks"].get(spec.network_ref or "", {})
            cidr = net.get("cidr", "10.200.0.0/24")
            ip = self._alloc_ip(cidr, self._state["ip_counter"])
            self._state["domains"][ref] = {
                "name": spec.name, "status": VMStatus.defined.value,
                "vcpu": spec.vcpu, "memory_mb": spec.memory_mb, "arch": spec.arch,
                "ip": ip, "vnc_port": self._state["vnc_counter"],
                "overlay": spec.overlay_path, "network": spec.network_ref,
                "snapshots": {},
            }
            self._save()
            return ref

    def _require(self, ref: str) -> dict:
        dom = self._state["domains"].get(ref)
        if dom is None:
            raise DriverError(f"Unknown domain {ref}")
        return dom

    def start(self, ref: str) -> None:
        with self._lock:
            dom = self._require(ref)
            dom["status"] = VMStatus.running.value
            self._save()

    def stop(self, ref: str, force: bool = False) -> None:
        with self._lock:
            dom = self._require(ref)
            dom["status"] = VMStatus.stopped.value
            self._save()

    def reboot(self, ref: str) -> None:
        with self._lock:
            dom = self._require(ref)
            dom["status"] = VMStatus.running.value
            self._save()

    def pause(self, ref: str) -> None:
        with self._lock:
            self._require(ref)["status"] = VMStatus.paused.value
            self._save()

    def resume(self, ref: str) -> None:
        with self._lock:
            self._require(ref)["status"] = VMStatus.running.value
            self._save()

    def delete(self, ref: str) -> None:
        with self._lock:
            self._state["domains"].pop(ref, None)
            self._save()

    def status(self, ref: str) -> VMStatus:
        with self._lock:
            dom = self._state["domains"].get(ref)
            if dom is None:
                return VMStatus.deleted
            return VMStatus(dom["status"])

    def get_ip(self, ref: str) -> str | None:
        with self._lock:
            dom = self._state["domains"].get(ref)
            if not dom or dom["status"] != VMStatus.running.value:
                return None
            return dom.get("ip")

    def console(self, ref: str) -> ConsoleInfo:
        dom = self._require(ref)
        return ConsoleInfo(kind="vnc", host="127.0.0.1", port=dom.get("vnc_port"))

    def snapshot_create(self, ref: str, name: str, kind: str = "disk") -> str:
        with self._lock:
            dom = self._require(ref)
            dom["snapshots"][name] = {"kind": kind, "state": dom["status"]}
            self._save()
            return name

    def snapshot_restore(self, ref: str, name: str) -> None:
        with self._lock:
            dom = self._require(ref)
            if name not in dom["snapshots"]:
                raise DriverError(f"No snapshot {name}")
            dom["status"] = dom["snapshots"][name]["state"]
            self._save()

    def snapshot_delete(self, ref: str, name: str) -> None:
        with self._lock:
            self._require(ref)["snapshots"].pop(name, None)
            self._save()

    def list_domains(self) -> list[str]:
        with self._lock:
            return list(self._state["domains"].keys())

    @staticmethod
    def _alloc_ip(cidr: str, counter: int) -> str:
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            hosts = list(net.hosts())
            if not hosts:
                return "10.200.0.10"
            return str(hosts[counter % len(hosts)])
        except ValueError:
            return f"10.200.0.{counter % 250 + 2}"
