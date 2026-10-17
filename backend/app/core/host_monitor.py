"""Real host resource monitoring via psutil. No fabricated statistics."""
from __future__ import annotations

import platform
import shutil
import time

import psutil

from backend.app.core.config import get_settings


def host_stats() -> dict:
    s = get_settings()
    vm = psutil.virtual_memory()
    storage_dir = s.data_dir
    disk = shutil.disk_usage(str(storage_dir if storage_dir.exists() else storage_dir.parent))
    # cpu_percent with a short interval for an instantaneous-ish reading.
    cpu_percent = psutil.cpu_percent(interval=0.15)
    load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
    return {
        "timestamp": time.time(),
        "platform": platform.system(),
        "arch": platform.machine(),
        "cpu": {
            "percent": cpu_percent,
            "cores_logical": psutil.cpu_count(logical=True),
            "cores_physical": psutil.cpu_count(logical=False),
            "load_avg": list(load),
        },
        "memory": {
            "total_mb": round(vm.total / 1024 / 1024),
            "used_mb": round(vm.used / 1024 / 1024),
            "available_mb": round(vm.available / 1024 / 1024),
            "percent": vm.percent,
        },
        "storage": {
            # Distinguish real physical storage from virtual disk capacity.
            "path": str(storage_dir),
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
            "percent": round(disk.used / disk.total * 100, 1) if disk.total else 0,
        },
    }


def process_stats(pids: list[int]) -> dict[int, dict]:
    """Per-VM resource consumption for the given process ids."""
    out: dict[int, dict] = {}
    for pid in pids:
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                out[pid] = {
                    "cpu_percent": p.cpu_percent(interval=None),
                    "memory_mb": round(p.memory_info().rss / 1024 / 1024),
                    "status": p.status(),
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            out[pid] = {"cpu_percent": 0, "memory_mb": 0, "status": "gone"}
    return out
