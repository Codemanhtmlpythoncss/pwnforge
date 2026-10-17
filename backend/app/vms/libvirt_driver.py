"""Production libvirt/KVM driver for Debian hosts.

Uses the ``libvirt`` Python binding (Debian package ``python3-libvirt``).
Copy-on-write overlays are created with ``qemu-img create -b <base> -F qcow2``.
Isolated networks are real libvirt networks with no forward mode (no external
connectivity) unless NAT is explicitly requested.

This is the real virtualisation path. It is exercised on a Linux/KVM host; on
macOS the binding is absent, so the module imports lazily and the driver is
only constructed when selected. It is therefore UNVERIFIED on this dev machine
(documented in docs/SECURITY.md and the delivery report).
"""
from __future__ import annotations

import subprocess
import time
import xml.sax.saxutils as sx
from pathlib import Path

from backend.app.core.config import get_settings
from backend.app.database.models import VMStatus
from backend.app.vms.driver import (
    ConsoleInfo,
    CapacityError,
    DriverError,
    DriverUnsupported,
    HostCapabilities,
    VMDriver,
    VMSpec,
)

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
        self._uri = uri or get_settings().libvirt_uri
        self._conn = libvirt.open(self._uri)
        if self._conn is None:  # pragma: no cover
            raise DriverError(f"Failed to open libvirt connection {self._uri}")

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
            hardware_acceleration=True,
            features={
                "snapshots": True, "clone": True, "pause": True,
                "console": True, "networks": True, "copy_on_write": True,
            },
            notes=[f"libvirt {self._conn.getLibVersion()} via {self._uri}"],
        )

    # -- overlays -----------------------------------------------------------
    def create_overlay(self, base_image_path: str, overlay_path: str, size_gb: int) -> None:
        base = Path(base_image_path)
        if not base.exists():
            raise DriverError(f"Base image missing: {base_image_path}")
        Path(overlay_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "qemu-img", "create", "-q", "-f", "qcow2",
            "-F", "qcow2", "-b", str(base), overlay_path,
        ]
        self._run(cmd)

    def delete_overlay(self, overlay_path: str) -> None:
        p = Path(overlay_path)
        if p.exists():
            p.unlink()

    # -- networks -----------------------------------------------------------
    def create_network(self, name: str, cidr: str, mode: str, external: bool) -> str:  # pragma: no cover
        import ipaddress

        net = ipaddress.ip_network(cidr, strict=False)
        gateway = str(next(net.hosts()))
        dhcp_start = str(list(net.hosts())[1])
        dhcp_end = str(list(net.hosts())[-1])
        forward = ""
        if external and mode == "nat":
            forward = "<forward mode='nat'/>"
        xml = f"""
<network>
  <name>{sx.escape(name)}</name>
  {forward}
  <bridge name='virbr-{sx.escape(name)[:8]}' stp='on' delay='0'/>
  <ip address='{gateway}' netmask='{net.netmask}'>
    <dhcp><range start='{dhcp_start}' end='{dhcp_end}'/></dhcp>
  </ip>
</network>""".strip()
        netobj = self._conn.networkDefineXML(xml)
        netobj.setAutostart(False)
        netobj.create()
        return name

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
        vnc = ""
        if not spec.headless:
            vnc = "<graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'/>"
        net = ""
        if spec.network_ref:
            mac = f"<mac address='{spec.mac}'/>" if spec.mac else ""
            net = (f"<interface type='network'>{mac}"
                   f"<source network='{sx.escape(spec.network_ref)}'/>"
                   f"<model type='virtio'/></interface>")
        cloud = ""
        if spec.cloud_init_iso:
            cloud = (f"<disk type='file' device='cdrom'>"
                     f"<driver name='qemu' type='raw'/>"
                     f"<source file='{sx.escape(spec.cloud_init_iso)}'/>"
                     f"<target dev='sdc' bus='sata'/><readonly/></disk>")
        xml = f"""
<domain type='kvm'>
  <name>{sx.escape(spec.name)}</name>
  <memory unit='MiB'>{spec.memory_mb}</memory>
  <vcpu>{spec.vcpu}</vcpu>
  <os><type arch='{spec.arch}' machine='q35'>hvm</type><boot dev='hd'/></os>
  <features><acpi/><apic/></features>
  <cpu mode='host-passthrough' check='none'/>
  <devices>
    <emulator>/usr/bin/qemu-system-{spec.arch}</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{sx.escape(spec.overlay_path)}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    {cloud}
    {net}
    <serial type='pty'><target port='0'/></serial>
    <console type='pty'><target type='serial' port='0'/></console>
    {vnc}
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
    </channel>
  </devices>
</domain>""".strip()
        dom = self._conn.defineXML(xml)
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
        try:
            dom.undefineFlags(self._libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)
        except self._libvirt.libvirtError:
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

    @staticmethod
    def _run(cmd: list[str]) -> None:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise DriverError(f"command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
