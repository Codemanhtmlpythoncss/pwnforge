"""Virtualisation driver contract.

The same orchestration code runs against any driver that implements this
interface. A driver reports its real capabilities; the orchestration layer
refuses operations a driver cannot honestly perform rather than faking them.

Drivers shipped:
  * libvirt  - production path for Debian/KVM hosts (``LibvirtDriver``).
  * qemu     - direct QEMU process management where libvirt is absent.
  * simulation - deterministic, clearly-labelled fake for hosts with no
                 hypervisor (e.g. macOS dev boxes, CI). It never claims to be
                 a real hypervisor; instances created on it are flagged
                 ``driver="simulation"`` and surfaced as simulated in the UI.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field

from backend.app.database.models import VMStatus


class DriverError(Exception):
    """Base class for driver failures."""


class DriverUnsupported(DriverError):
    """Raised when a driver cannot perform a requested capability."""


class CapacityError(DriverError):
    """Raised when the host lacks resources for an operation."""


@dataclass(frozen=True)
class HostCapabilities:
    driver: str
    platform: str                 # linux | darwin | ...
    arch: str                     # x86_64 | aarch64
    cpu_count: int
    total_memory_mb: int
    real_virtualization: bool     # True only for libvirt/qemu that can boot a guest
    hardware_acceleration: bool   # KVM (linux) or HVF (macOS)
    features: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class VMSpec:
    name: str
    vcpu: int
    memory_mb: int
    arch: str = "x86_64"
    base_image_path: str | None = None
    overlay_path: str | None = None
    disk_gb: int = 10
    network_ref: str | None = None
    mac: str | None = None
    cloud_init_iso: str | None = None
    headless: bool = True


@dataclass
class ConsoleInfo:
    kind: str           # vnc | spice | serial | none
    host: str
    port: int | None
    token: str | None = None


class VMDriver(abc.ABC):
    """Abstract hypervisor driver."""

    name: str = "abstract"

    @abc.abstractmethod
    def capabilities(self) -> HostCapabilities: ...

    # --- image / overlay management ---
    @abc.abstractmethod
    def create_overlay(self, base_image_path: str, overlay_path: str, size_gb: int) -> None:
        """Create a copy-on-write overlay backed by ``base_image_path``."""

    @abc.abstractmethod
    def delete_overlay(self, overlay_path: str) -> None: ...

    # --- networks ---
    @abc.abstractmethod
    def create_network(self, name: str, cidr: str, mode: str, external: bool) -> str:
        """Create an isolated virtual network; return a driver reference."""

    @abc.abstractmethod
    def delete_network(self, ref: str) -> None: ...

    # --- domain lifecycle ---
    @abc.abstractmethod
    def define(self, spec: VMSpec) -> str:
        """Define (but do not start) a domain; return a driver reference."""

    @abc.abstractmethod
    def start(self, ref: str) -> None: ...

    @abc.abstractmethod
    def stop(self, ref: str, force: bool = False) -> None: ...

    @abc.abstractmethod
    def reboot(self, ref: str) -> None: ...

    def pause(self, ref: str) -> None:
        raise DriverUnsupported("pause not supported by this driver")

    def resume(self, ref: str) -> None:
        raise DriverUnsupported("resume not supported by this driver")

    @abc.abstractmethod
    def delete(self, ref: str) -> None: ...

    @abc.abstractmethod
    def status(self, ref: str) -> VMStatus:
        """Return the *actual* domain status queried from the hypervisor."""

    @abc.abstractmethod
    def get_ip(self, ref: str) -> str | None: ...

    def console(self, ref: str) -> ConsoleInfo:
        raise DriverUnsupported("console not supported by this driver")

    # --- snapshots ---
    def snapshot_create(self, ref: str, name: str, kind: str = "disk") -> str:
        raise DriverUnsupported("snapshots not supported by this driver")

    def snapshot_restore(self, ref: str, name: str) -> None:
        raise DriverUnsupported("snapshots not supported by this driver")

    def snapshot_delete(self, ref: str, name: str) -> None:
        raise DriverUnsupported("snapshots not supported by this driver")

    @abc.abstractmethod
    def list_domains(self) -> list[str]:
        """Return driver references for every domain the driver knows about."""
