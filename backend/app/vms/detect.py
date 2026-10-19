"""Host virtualisation capability detection and driver selection."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def probe_host() -> dict:
    """Inspect the host for virtualisation support. Pure inspection, no side effects."""
    system = platform.system().lower()
    arch = platform.machine()
    info: dict = {
        "platform": system,
        "arch": arch,
        "has_kvm": False,
        "has_hvf": False,
        "has_libvirt_py": _module_present("libvirt"),
        "has_virsh": shutil.which("virsh") is not None,
        "has_qemu_img": shutil.which("qemu-img") is not None,
        "qemu_system": _qemu_system_binary(arch),
        "notes": [],
    }
    if system == "linux":
        info["has_kvm"] = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
        if not os.path.exists("/dev/kvm"):
            info["notes"].append("/dev/kvm not present: KVM acceleration unavailable.")
        elif not info["has_kvm"]:
            info["notes"].append("/dev/kvm present but not accessible (check kvm group membership).")
    elif system == "darwin":
        info["has_hvf"] = True
        info["notes"].append(
            "macOS host: the production libvirt VM backend requires Linux."
        )
    return info


def select_driver_name(configured: str = "auto") -> str:
    """Select a real VM backend; report unavailable instead of silently simulating."""
    host = probe_host()
    if configured and configured != "auto":
        return configured
    if (host["platform"] == "linux" and host["qemu_system"] and host["has_qemu_img"]
            and (host["has_libvirt_py"] or host["has_virsh"])):
        # Libvirt can run genuine QEMU guests with TCG when KVM is unavailable.
        return "libvirt"
    return "unavailable"


def _module_present(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None


def _qemu_system_binary(arch: str) -> str | None:
    candidates = []
    if arch in ("x86_64", "amd64"):
        candidates = ["qemu-system-x86_64"]
    elif arch in ("aarch64", "arm64"):
        candidates = ["qemu-system-aarch64"]
    else:
        candidates = [f"qemu-system-{arch}"]
    for c in candidates:
        if shutil.which(c):
            return c
    return None


def host_summary() -> str:
    h = probe_host()
    lines = [
        f"platform={h['platform']} arch={h['arch']}",
        f"kvm={h['has_kvm']} hvf={h['has_hvf']} libvirt_py={h['has_libvirt_py']} "
        f"virsh={h['has_virsh']} qemu_img={h['has_qemu_img']} qemu={h['qemu_system']}",
        f"selected_driver={select_driver_name()}",
    ]
    lines.extend(f"note: {n}" for n in h["notes"])
    return "\n".join(lines)
