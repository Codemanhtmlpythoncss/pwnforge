"""Production libvirt/KVM driver for Debian hosts.

Uses the ``libvirt`` Python binding (Debian package ``python3-libvirt``).
Copy-on-write overlays are created with ``qemu-img create -b <base> -F qcow2``.
Isolated networks are real libvirt networks with no forward mode (no external
connectivity) unless NAT is explicitly requested.

Both x86_64 hosts (q35, BIOS) and arm64 hosts such as a Raspberry Pi (``virt``
machine, UEFI firmware from ``qemu-efi-aarch64``) are supported. Guests get
their cloud-init seed as a read-only virtio disk and a serial console that the
website reaches through a libvirt stream (``open_console``), never a host shell.
On macOS the binding is absent, so the module imports lazily and the driver is
only constructed when selected.
"""
from __future__ import annotations

import hashlib
import json
import queue
import subprocess
import threading
import time
import xml.sax.saxutils as sx
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.database.models import VMStatus
from backend.app.vms.detect import probe_host
from backend.app.vms.driver import (
    ConsoleInfo,
    CapacityError,
    DriverError,
    DriverUnsupported,
    HostCapabilities,
    VMDriver,
    VMSpec,
)

BUILD_NETWORK = "pwnforge-build"        # NAT, only while a role image is being prepared
BUILD_CIDR = "10.254.254.0/24"
_event_loop_started = False
_event_loop_lock = threading.Lock()


def _start_event_loop(libvirt) -> None:
    """Console streams need libvirt's event loop: register it once, run it on a daemon thread."""
    global _event_loop_started
    with _event_loop_lock:
        if _event_loop_started:
            return
        libvirt.virEventRegisterDefaultImpl()

        def run() -> None:
            while True:
                libvirt.virEventRunDefaultImpl()
        threading.Thread(target=run, name="libvirt-events", daemon=True).start()
        _event_loop_started = True


def arch_of(arch: str) -> str:
    return "aarch64" if (arch or "").lower() in ("aarch64", "arm64") else "x86_64"


def bridge_name(network: str) -> str:
    """A unique Linux bridge name (15 characters at most) for a libvirt network."""
    return "pfbr" + hashlib.sha1(network.encode()).hexdigest()[:10]


def domain_xml(spec: VMSpec, *, hardware_acceleration: bool = True) -> str:
    """Build a real libvirt guest definition for KVM or QEMU's software emulator."""
    arch = arch_of(spec.arch)
    if arch == "aarch64":
        os_xml = ("<os firmware='efi'><type arch='aarch64' machine='virt'>hvm</type><boot dev='hd'/></os>")
        gic = "host" if hardware_acceleration else "3"
        features = f"<features><acpi/><gic version='{gic}'/></features>"
    else:
        os_xml = "<os><type arch='x86_64' machine='q35'>hvm</type><boot dev='hd'/></os>"
        features = "<features><acpi/><apic/></features>"
    domain_type = "kvm" if hardware_acceleration else "qemu"
    cpu = "<cpu mode='host-passthrough' check='none'/>" if hardware_acceleration else ""
    seed = ""
    if spec.cloud_init_iso:
        seed = (f"<disk type='file' device='disk'><driver name='qemu' type='raw'/>"
                f"<source file='{sx.escape(spec.cloud_init_iso)}'/>"
                f"<target dev='vdb' bus='virtio'/><readonly/></disk>")
    net = ""
    if spec.network_ref:
        mac = f"<mac address='{sx.escape(spec.mac)}'/>" if spec.mac else ""
        net = (f"<interface type='network'>{mac}"
               f"<source network='{sx.escape(spec.network_ref)}'/>"
               f"<model type='virtio'/></interface>")
    gfx = ""
    if not spec.headless:
        gfx = ("<graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'/>"
               "<video><model type='virtio'/></video>"
               "<input type='tablet' bus='usb'/><input type='keyboard' bus='usb'/>")
    return f"""
<domain type='{domain_type}'>
  <name>{sx.escape(spec.name)}</name>
  <memory unit='MiB'>{int(spec.memory_mb)}</memory>
  <vcpu>{int(spec.vcpu)}</vcpu>
  {os_xml}
  {features}
  {cpu}
  <on_poweroff>destroy</on_poweroff>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{sx.escape(spec.overlay_path or "")}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    {seed}
    {net}
    <serial type='pty'><target port='0'/></serial>
    <console type='pty'><target type='serial' port='0'/></console>
    {gfx}
    <channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>
    <rng model='virtio'><backend model='random'>/dev/urandom</backend></rng>
  </devices>
</domain>""".strip()


def network_xml(name: str, cidr: str, nat: bool = False) -> str:
    """An isolated network (DHCP from the host, no route out) unless ``nat``."""
    import ipaddress

    net = ipaddress.ip_network(cidr, strict=False)
    hosts = list(net.hosts())
    forward = "<forward mode='nat'/>" if nat else ""
    return f"""
<network>
  <name>{sx.escape(name)}</name>
  {forward}
  <bridge name='{bridge_name(name)}' stp='on' delay='0'/>
  <ip address='{hosts[0]}' netmask='{net.netmask}'>
    <dhcp><range start='{hosts[1]}' end='{hosts[-1]}'/></dhcp>
  </ip>
</network>""".strip()


def _virtual_size(path: Path) -> int:
    try:
        out = subprocess.run(["qemu-img", "info", "--output=json", "-U", str(path)],
                             capture_output=True, text=True, timeout=60)
        return int(json.loads(out.stdout or "{}").get("virtual-size") or 0)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


class ConsoleStream:
    """A guest's serial console over a libvirt stream: ``read`` returns bytes (b"" = nothing yet, None = closed)."""

    def __init__(self, libvirt, conn, dom) -> None:
        self._lv = libvirt
        self._q: queue.Queue = queue.Queue()
        self._closed = False
        self._st = conn.newStream(libvirt.VIR_STREAM_NONBLOCK)
        dom.openConsole(None, self._st, libvirt.VIR_DOMAIN_CONSOLE_FORCE)
        events = (libvirt.VIR_STREAM_EVENT_READABLE | libvirt.VIR_STREAM_EVENT_ERROR
                  | libvirt.VIR_STREAM_EVENT_HANGUP)
        self._st.eventAddCallback(events, self._on_event, None)

    def _on_event(self, stream, events, _opaque) -> None:
        lv = self._lv
        if events & lv.VIR_STREAM_EVENT_READABLE:
            try:
                data = stream.recv(4096)
            except lv.libvirtError:
                data = None
            if isinstance(data, (bytes, bytearray)):
                if data:
                    self._q.put(bytes(data))
                    return
                data = None          # end of stream
            if data is None:
                self._finish()
                return
            return                   # -2: nothing to read after all
        if events & (lv.VIR_STREAM_EVENT_ERROR | lv.VIR_STREAM_EVENT_HANGUP):
            self._finish()

    def _finish(self) -> None:
        if not self._closed:
            self._closed = True
            self._q.put(None)

    def read(self, timeout: float = 1.0):
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None if self._closed and self._q.empty() else b""

    def write(self, data: bytes) -> None:
        if self._closed:
            return
        view, deadline = memoryview(data), time.monotonic() + 5
        while view and time.monotonic() < deadline:
            try:
                n = self._st.send(bytes(view))
            except self._lv.libvirtError:
                self._finish()
                return
            if n == -2:
                time.sleep(0.02)
                continue
            view = view[n:]

    def close(self) -> None:
        try:
            self._st.eventRemoveCallback()
        except self._lv.libvirtError:
            pass
        try:
            self._st.abort()
        except self._lv.libvirtError:
            pass
        self._finish()


_STATE_MAP = {
    0: VMStatus.defined,    # VIR_DOMAIN_NOSTATE
    1: VMStatus.running,    # VIR_DOMAIN_RUNNING
    2: VMStatus.paused,     # VIR_DOMAIN_BLOCKED
    3: VMStatus.paused,     # VIR_DOMAIN_PAUSED
    4: VMStatus.stopping,   # VIR_DOMAIN_SHUTDOWN
    5: VMStatus.stopped,    # VIR_DOMAIN_SHUTOFF
    6: VMStatus.error,      # VIR_DOMAIN_CRASHED
    7: VMStatus.paused,     # VIR_DOMAIN_PMSUSPENDED
}


class LibvirtDriver(VMDriver):
    name = "libvirt"

    def __init__(self, uri: str | None = None) -> None:
        try:
            import libvirt  # type: ignore
        except ImportError as exc:  # pragma: no cover - platform dependent
            raise DriverUnsupported(
                "python3-libvirt is not installed; cannot use the libvirt driver"
            ) from exc
        self._libvirt = libvirt
        _start_event_loop(libvirt)
        self._uri = uri or get_settings().libvirt_uri
        self._conn = libvirt.open(self._uri)
        if self._conn is None:  # pragma: no cover
            raise DriverError(f"Failed to open libvirt connection {self._uri}")
        self._hardware_acceleration = probe_host()["has_kvm"]

    # -- capabilities -------------------------------------------------------
    def capabilities(self) -> HostCapabilities:  # pragma: no cover - needs host
        info = self._conn.getInfo()
        return HostCapabilities(
            driver=self.name,
            platform="linux",
            arch=info[0],
            cpu_count=info[2],
            total_memory_mb=int(info[1]),
            real_virtualization=True,
            hardware_acceleration=self._hardware_acceleration,
            features={
                "snapshots": True, "clone": True, "pause": True,
                "console": True, "networks": True, "copy_on_write": True,
            },
            notes=[
                f"libvirt {self._conn.getLibVersion()} via {self._uri}",
                *([] if self._hardware_acceleration else [
                    "Real guests use QEMU TCG software emulation because KVM is unavailable; expect slower boot and runtime."
                ]),
            ],
        )

    # -- overlays -----------------------------------------------------------
    def create_overlay(self, base_image_path: str, overlay_path: str, size_gb: int) -> None:
        base = Path(base_image_path)
        if not base.exists():
            raise DriverError(f"Base image missing: {base_image_path}")
        Path(overlay_path).parent.mkdir(parents=True, exist_ok=True)
        # As big as the profile asks (cloud images are small; cloud-init grows the root filesystem to fit),
        # never smaller than the image it's based on.
        size = max(int(size_gb) << 30, _virtual_size(base))
        cmd = [
            "qemu-img", "create", "-q", "-f", "qcow2",
            "-F", "qcow2", "-b", str(base), overlay_path, str(size),
        ]
        self._run(cmd)
        # the learner's disk: only PwnForge (and, while it runs, libvirt's QEMU user) may read it
        Path(overlay_path).chmod(0o640)

    def delete_overlay(self, overlay_path: str) -> None:
        p = Path(overlay_path)
        if p.exists():
            p.unlink()

    # -- networks -----------------------------------------------------------
    def create_network(self, name: str, cidr: str, mode: str, external: bool) -> str:  # pragma: no cover
        ref = name if name.startswith("pwnforge-") else f"pwnforge-{name}"
        self.delete_network(ref)             # a stale one left by a crash
        netobj = self._conn.networkDefineXML(network_xml(ref, cidr, nat=bool(external and mode == "nat")))
        netobj.setAutostart(False)
        netobj.create()
        return ref

    def delete_network(self, ref: str) -> None:  # pragma: no cover
        try:
            netobj = self._conn.networkLookupByName(ref)
        except self._libvirt.libvirtError:
            return
        if netobj.isActive():
            netobj.destroy()
        netobj.undefine()

    # -- domains ------------------------------------------------------------
    def define(self, spec: VMSpec) -> str:  # pragma: no cover - needs host
        if not spec.overlay_path:
            raise DriverError("libvirt domains require an overlay disk path")
        try:
            old = self._conn.lookupByName(spec.name)       # a stale definition left by a crash
        except self._libvirt.libvirtError:
            old = None
        if old is not None:
            self.delete(spec.name)
        dom = self._conn.defineXML(domain_xml(
            spec, hardware_acceleration=self._hardware_acceleration))
        return dom.name()

    def _dom(self, ref: str):  # pragma: no cover
        try:
            return self._conn.lookupByName(ref)
        except self._libvirt.libvirtError as exc:
            raise DriverError(f"Unknown domain {ref}: {exc}") from exc

    def start(self, ref: str) -> None:  # pragma: no cover
        dom = self._dom(ref)
        if not dom.isActive():
            dom.create()

    def stop(self, ref: str, force: bool = False) -> None:  # pragma: no cover
        dom = self._dom(ref)
        if not dom.isActive():
            return
        if force:
            dom.destroy()
        else:
            dom.shutdown()

    def reboot(self, ref: str) -> None:  # pragma: no cover
        self._dom(ref).reboot()

    def pause(self, ref: str) -> None:  # pragma: no cover
        self._dom(ref).suspend()

    def resume(self, ref: str) -> None:  # pragma: no cover
        self._dom(ref).resume()

    def delete(self, ref: str) -> None:  # pragma: no cover
        dom = self._dom(ref)
        if dom.isActive():
            dom.destroy()
        lv = self._libvirt
        # NVRAM: an arm64 (UEFI) guest's firmware variables, kept by libvirt per domain
        flags = lv.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA | getattr(lv, "VIR_DOMAIN_UNDEFINE_NVRAM", 0)
        try:
            dom.undefineFlags(flags)
        except lv.libvirtError:
            dom.undefine()

    def status(self, ref: str) -> VMStatus:  # pragma: no cover
        try:
            state, _ = self._dom(ref).state()
        except DriverError:
            return VMStatus.deleted
        return _STATE_MAP.get(state, VMStatus.error)

    def get_ip(self, ref: str) -> str | None:  # pragma: no cover
        dom = self._dom(ref)
        if not dom.isActive():
            return None
        try:
            ifaces = dom.interfaceAddresses(
                self._libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE
            )
        except self._libvirt.libvirtError:
            try:
                ifaces = dom.interfaceAddresses(
                    self._libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT
                )
            except self._libvirt.libvirtError:
                return None
        for data in ifaces.values():
            for addr in data.get("addrs", []):
                if addr.get("type") == 0:  # IPv4
                    return addr.get("addr")
        return None

    def console(self, ref: str) -> ConsoleInfo:  # pragma: no cover
        import xml.etree.ElementTree as ET

        dom = self._dom(ref)
        root = ET.fromstring(dom.XMLDesc())
        g = root.find(".//graphics[@type='vnc']")
        if g is None:
            raise DriverUnsupported("domain has no VNC graphics device")
        return ConsoleInfo(kind="vnc", host="127.0.0.1", port=int(g.get("port", "-1")))

    def snapshot_create(self, ref: str, name: str, kind: str = "disk") -> str:  # pragma: no cover
        dom = self._dom(ref)
        disk_only = "" if kind in ("memory", "both") else "<disk-only/>"
        xml = f"<domainsnapshot><name>{sx.escape(name)}</name>{disk_only}</domainsnapshot>"
        flags = 0
        if kind == "disk":
            flags = self._libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_DISK_ONLY
        dom.snapshotCreateXML(xml, flags)
        return name

    def snapshot_restore(self, ref: str, name: str) -> None:  # pragma: no cover
        dom = self._dom(ref)
        snap = dom.snapshotLookupByName(name)
        dom.revertToSnapshot(snap)

    def snapshot_delete(self, ref: str, name: str) -> None:  # pragma: no cover
        dom = self._dom(ref)
        dom.snapshotLookupByName(name).delete()

    def list_domains(self) -> list[str]:  # pragma: no cover
        return [d.name() for d in self._conn.listAllDomains()]

    # -- serial console -------------------------------------------------------
    def open_console(self, ref: str) -> ConsoleStream:  # pragma: no cover - needs host
        dom = self._dom(ref)
        if not dom.isActive():
            raise DriverError("the machine isn't running")
        return ConsoleStream(self._libvirt, self._conn, dom)

    # -- preparing a role image -------------------------------------------------
    def run_build(self, *, name: str, arch: str, disk: str, seed: str, ok_marker: str, fail_marker: str,
                  timeout_s: int, log=None) -> tuple[bool, str]:  # pragma: no cover - needs host
        """Boot ``disk`` with ``seed`` on a temporary NAT network until it powers itself off.

        Returns (ok, the console's last lines). ok means the guest printed ``ok_marker`` and then shut down."""
        from backend.app.vms.driver import VMSpec as _Spec

        log = log or (lambda msg: None)
        self.create_network(BUILD_NETWORK, BUILD_CIDR, "nat", True)
        ref = None
        con = None
        text, ok, failed = "", False, False
        try:
            ref = self.define(_Spec(name=name, vcpu=2, memory_mb=1536, arch=arch, overlay_path=disk,
                                    cloud_init_iso=seed, network_ref=BUILD_NETWORK, headless=True))
            self.start(ref)
            con = self.open_console(ref)
            start = last_note = time.monotonic()
            while time.monotonic() - start < timeout_s:
                chunk = con.read(1.0)
                if chunk:
                    text = (text + chunk.decode("utf-8", "replace"))[-20000:]
                    ok = ok or ok_marker in text
                    failed = failed or fail_marker in text
                if not self._dom(ref).isActive():
                    break
                if time.monotonic() - last_note > 30:
                    last_note = time.monotonic()
                    log("Preparing the machine image (%d min so far)" % ((last_note - start) // 60))
            else:
                text += "\n[timed out after %d minutes]" % (timeout_s // 60)
            if self._dom(ref).isActive():
                self._dom(ref).destroy()
                ok = False
            return ok and not failed, _console_tail(text)
        finally:
            if con is not None:
                con.close()
            if ref is not None:
                try:
                    self.delete(ref)
                except DriverError:
                    pass
            self.delete_network(BUILD_NETWORK)

    @staticmethod
    def _run(cmd: list[str]) -> None:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise DriverError(f"command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")


def _console_tail(text: str, lines: int = 25) -> str:
    """The last non-empty lines of a console log, without terminal escape sequences."""
    import re

    clean = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\r", "", text)
    return "\n".join([line for line in clean.splitlines() if line.strip()][-lines:])
