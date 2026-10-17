"""Driver factory with caching and capability reporting."""
from __future__ import annotations

import threading

from backend.app.core.config import get_settings
from backend.app.vms.detect import select_driver_name
from backend.app.vms.driver import HostCapabilities, VMDriver
from backend.app.vms.simulation_driver import SimulationDriver

_lock = threading.Lock()
_cache: dict[str, VMDriver] = {}


def get_driver(name: str | None = None) -> VMDriver:
    """Return a cached driver instance. Falls back to simulation on failure."""
    resolved = name or select_driver_name(get_settings().vm_driver)
    with _lock:
        if resolved in _cache:
            return _cache[resolved]
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
    return SimulationDriver()


def active_capabilities() -> HostCapabilities:
    return get_driver().capabilities()


def reset_cache() -> None:
    with _lock:
        _cache.clear()
