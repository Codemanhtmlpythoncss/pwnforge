"""Direct QEMU process driver.

Used on Linux hosts that have QEMU/qemu-img but not libvirt. VMs are real
QEMU processes; lifecycle is managed through a per-domain QMP control socket
and status is read from the live process, never assumed. Copy-on-write
overlays are created with ``qemu-img``.

Networking defaults to QEMU user-mode (slirp) for a single VM. Multi-VM
isolated networks use QEMU socket/mcast VLANs. Bridged isolation that needs
root is delegated to the libvirt driver on production hosts.

qemu-img overlay creation is verifiable on any host with qemu-img (including
this dev Mac); booting a guest is not verified here because no base image is
present and the host is macOS.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import time
from pathlib import Path

import psutil

from backend.app.core.config import get_settings
from backend.app.database.models import VMStatus
from backend.app.vms.detect import probe_host
from backend.app.vms.driver import (
    ConsoleInfo,
    DriverError,
    DriverUnsupported,
    HostCapabilities,
    VMDriver,
    VMSpec,
)


class QemuDriver(VMDriver):
    name = "qemu"

    def __init__(self, run_dir: Path | None = None) -> None:
        if not shutil.which("qemu-img"):
            raise DriverUnsupported("qemu-img not found")
        host = probe_host()
        self._qemu = host["qemu_system"]
        if not self._qemu:
            raise DriverUnsupported("no qemu-system binary for this architecture")
        self._accel = "kvm" if host["has_kvm"] else ("hvf" if host["has_hvf"] else "tcg")
        self._run_dir = run_dir or (get_settings().data_dir / "qemu")
        self._run_dir.mkdir(parents=True, exist_ok=True)

    def capabilities(self) -> HostCapabilities:
        return HostCapabilities(
            driver=self.name,
            platform=platform.system().lower(),
            arch=platform.machine(),
            cpu_count=psutil.cpu_count(logical=True) or 1,
            total_memory_mb=int(psutil.virtual_memory().total / (1024 * 1024)),
            real_virtualization=True,
            hardware_acceleration=self._accel in ("kvm", "hvf"),
            features={
                "snapshots": True, "clone": True, "pause": True,
                "console": True, "networks": True, "copy_on_write": True,
            },
            notes=[
                f"QEMU {self._qemu} accel={self._accel}",
                "User-mode networking by default; isolated VLANs via socket.",
            ],
        )

    # -- overlays (verifiable) ---------------------------------------------
    def create_overlay(self, base_image_path: str, overlay_path: str, size_gb: int) -> None:
        base = Path(base_image_path)
        if not base.exists():
            raise DriverError(f"Base image missing: {base_image_path}")
        Path(overlay_path).parent.mkdir(parents=True, exist_ok=True)
        self._run(["qemu-img", "create", "-q", "-f", "qcow2",
                   "-F", "qcow2", "-b", str(base), overlay_path])

    def delete_overlay(self, overlay_path: str) -> None:
        p = Path(overlay_path)
        if p.exists():
            p.unlink()

    # -- networks -----------------------------------------------------------
    def create_network(self, name: str, cidr: str, mode: str, external: bool) -> str:
        # Socket VLAN hub identified by a deterministic port offset.
        port = 20000 + (abs(hash(name)) % 20000)
        meta = self._run_dir / f"net-{name}.json"
        meta.write_text(json.dumps({"name": name, "cidr": cidr, "mode": mode,
                                    "external": external, "mcast_port": port}))
        return name

    def delete_network(self, ref: str) -> None:
        meta = self._run_dir / f"net-{ref}.json"
        if meta.exists():
            meta.unlink()

    # -- domains ------------------------------------------------------------
    def _paths(self, ref: str) -> tuple[Path, Path, Path]:
        return (self._run_dir / f"{ref}.pid",
                self._run_dir / f"{ref}.qmp",
                self._run_dir / f"{ref}.json")

    def define(self, spec: VMSpec) -> str:
        ref = spec.name
        _, _, meta = self._paths(ref)
        meta.write_text(json.dumps({
            "name": spec.name, "vcpu": spec.vcpu, "memory_mb": spec.memory_mb,
            "arch": spec.arch, "overlay": spec.overlay_path, "network": spec.network_ref,
            "headless": spec.headless, "cloud_init": spec.cloud_init_iso,
        }))
        return ref

    def start(self, ref: str) -> None:
        pidfile, qmp, meta = self._paths(ref)
        if not meta.exists():
            raise DriverError(f"Domain not defined: {ref}")
        cfg = json.loads(meta.read_text())
        if not cfg.get("overlay"):
            raise DriverError("QEMU domain requires an overlay disk")
        if qmp.exists():
            qmp.unlink()
        cmd = [
            self._qemu, "-name", ref,
            "-machine", "q35" if cfg["arch"] == "x86_64" else "virt",
            "-accel", self._accel,
            "-m", str(cfg["memory_mb"]), "-smp", str(cfg["vcpu"]),
            "-drive", f"file={cfg['overlay']},if=virtio,format=qcow2",
            "-qmp", f"unix:{qmp},server,nowait",
            "-pidfile", str(pidfile),
            "-daemonize",
        ]
        if cfg.get("cloud_init"):
            cmd += ["-drive", f"file={cfg['cloud_init']},if=virtio,format=raw,readonly=on"]
        if cfg.get("network"):
            port = self._net_port(cfg["network"])
            cmd += ["-netdev", f"socket,id=n0,mcast=230.0.0.1:{port}",
                    "-device", "virtio-net-pci,netdev=n0"]
        else:
            cmd += ["-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0"]
        if cfg.get("headless", True):
            cmd += ["-display", "none", "-vnc", "127.0.0.1:0,to=100"]
        else:
            cmd += ["-vnc", "127.0.0.1:0,to=100"]
        self._run(cmd)

    def stop(self, ref: str, force: bool = False) -> None:
        pid = self._pid(ref)
        if pid is None:
            return
        if force:
            self._qmp(ref, {"execute": "quit"}, optional=True)
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            if not self._qmp(ref, {"execute": "system_powerdown"}, optional=True):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    def reboot(self, ref: str) -> None:
        if not self._qmp(ref, {"execute": "system_reset"}, optional=True):
            raise DriverError("reboot failed: QMP unavailable")

    def pause(self, ref: str) -> None:
        self._qmp(ref, {"execute": "stop"})

    def resume(self, ref: str) -> None:
        self._qmp(ref, {"execute": "cont"})

    def delete(self, ref: str) -> None:
        self.stop(ref, force=True)
        for p in self._paths(ref):
            if p.exists():
                p.unlink()

    def status(self, ref: str) -> VMStatus:
        pidfile, _, meta = self._paths(ref)
        if not meta.exists():
            return VMStatus.deleted
        pid = self._pid(ref)
        if pid is None or not psutil.pid_exists(pid):
            return VMStatus.stopped
        resp = self._qmp(ref, {"execute": "query-status"}, optional=True, want_response=True)
        if isinstance(resp, dict):
            st = resp.get("return", {}).get("status")
            if st == "running":
                return VMStatus.running
            if st in ("paused", "suspended"):
                return VMStatus.paused
            if st in ("shutdown", "guest-panicked"):
                return VMStatus.stopped
        return VMStatus.running  # process alive, QMP not yet ready

    def get_ip(self, ref: str) -> str | None:
        if self.status(ref) != VMStatus.running:
            return None
        # User-mode networking assigns a fixed guest IP.
        _, _, meta = self._paths(ref)
        cfg = json.loads(meta.read_text())
        if not cfg.get("network"):
            return "10.0.2.15"
        return None  # socket VLAN relies on in-guest DHCP; reported via guest agent

    def console(self, ref: str) -> ConsoleInfo:
        if self.status(ref) != VMStatus.running:
            raise DriverError("domain not running")
        return ConsoleInfo(kind="vnc", host="127.0.0.1", port=5900)

    def list_domains(self) -> list[str]:
        return [p.stem for p in self._run_dir.glob("*.json")
                if not p.name.startswith("net-")]

    # -- helpers ------------------------------------------------------------
    def _net_port(self, name: str) -> int:
        meta = self._run_dir / f"net-{name}.json"
        if meta.exists():
            return json.loads(meta.read_text())["mcast_port"]
        return 20000 + (abs(hash(name)) % 20000)

    def _pid(self, ref: str) -> int | None:
        pidfile, _, _ = self._paths(ref)
        try:
            return int(pidfile.read_text().strip())
        except (OSError, ValueError):
            return None

    def _qmp(self, ref: str, command: dict, optional: bool = False,
             want_response: bool = False):
        _, qmp, _ = self._paths(ref)
        if not qmp.exists():
            if optional:
                return None
            raise DriverError("QMP socket not available")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(str(qmp))
                s.recv(4096)  # greeting
                s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode() + b"\n")
                s.recv(4096)
                s.sendall(json.dumps(command).encode() + b"\n")
                data = s.recv(65536)
                if want_response:
                    for line in data.splitlines():
                        try:
                            obj = json.loads(line)
                            if "return" in obj or "error" in obj:
                                return obj
                        except json.JSONDecodeError:
                            continue
                return True
        except (OSError, socket.timeout) as exc:
            if optional:
                return None
            raise DriverError(f"QMP command failed: {exc}") from exc

    @staticmethod
    def _run(cmd: list[str]) -> None:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise DriverError(f"command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
