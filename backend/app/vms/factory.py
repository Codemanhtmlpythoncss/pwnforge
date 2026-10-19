"""Driver factory with caching and capability reporting."""
from __future__ import annotations

import threading
import platform

import psutil

from backend.app.core.config import get_settings
from backend.app.vms.detect import probe_host, select_driver_name
from backend.app.vms.driver import DriverUnsupported, HostCapabilities, VMDriver
from backend.app.vms.simulation_driver import SimulationDriver

_lock = threading.Lock()
_cache: dict[str, VMDriver | "_UnavailableDriver"] = {}


class _UnavailableDriver:
    """Read-only capability record used when no real VM backend is ready."""

    name = "unavailable"

    def __init__(self, note: str) -> None:
        self._note = note

    def capabilities(self) -> HostCapabilities:
        return HostCapabilities(
            driver=self.name,
            platform=platform.system().lower(),
            arch=platform.machine(),
            cpu_count=psutil.cpu_count(logical=True) or 1,
            total_memory_mb=int(psutil.virtual_memory().total / (1024 * 1024)),
            real_virtualization=False,
            hardware_acceleration=False,
            features={},
            notes=[self._note],
        )

    def __getattr__(self, _name: str):
        raise DriverUnsupported(self._note)


def get_driver(name: str | None = None) -> VMDriver | "_UnavailableDriver":
    """Return a real VM driver, or an unavailable status (never a fake VM in production)."""
    settings = get_settings()
    resolved = name or select_driver_name(settings.vm_driver)
    if resolved == "simulation" and settings.environment.lower() != "test":
        resolved = "unavailable"
    with _lock:
        if resolved in _cache:
            return _cache[resolved]
        if resolved == "unavailable":
            host = probe_host()
            if host["platform"] != "linux":
                note = "Real labs require a Linux host with QEMU, qemu-img, and libvirt; no simulated labs are created."
            else:
                note = ("Real labs aren't configured on this host. Install QEMU and libvirt, enable the "
                        "libvirt service, and use the 'Set up real machines' action; simulated labs are disabled.")
            driver = _UnavailableDriver(note)
        else:
            driver = _build(resolved)
        _cache[resolved] = driver
        return driver


def _build(name: str) -> VMDriver:
    if name == "libvirt":
        from backend.app.vms.libvirt_driver import LibvirtDriver

        return LibvirtDriver()
    if name == "qemu":
        from backend.app.vms.qemu_driver import QemuDriver

        return QemuDriver()
    if name == "simulation":
        return SimulationDriver()
    raise RuntimeError(f"Unknown VM driver configured: {name}")


def active_capabilities() -> HostCapabilities:
    return get_driver().capabilities()


def reset_cache() -> None:
    with _lock:
        _cache.clear()
