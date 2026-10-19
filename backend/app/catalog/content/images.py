"""Base image catalogue.

Debian is the primary foundation. Golden server images are CoW children of the
Debian base (parent_key), so a dozen role images cost roughly one base plus
small deltas. Windows images are referenced for completeness but require the
operator to supply appropriately licensed media; they are never downloaded
automatically. All images start as ``absent`` — nothing is fetched on import.

``source`` for cloud images is the upstream URL used ONLY when an operator runs
``pwnforge images fetch`` on the target host. Checksums should be filled in from
the upstream SHA256SUMS at fetch time / pinned per deployment.
"""
from __future__ import annotations

# (key, name, os_family, os_version, arch, source_kind, source, parent, build, virtual_gb)
BASE_IMAGES: list[dict] = [
    # --- Debian primary foundation ---
    dict(key="debian-13-base", name="Debian 13 Minimal (golden)", os_family="debian",
         os_version="13", arch="x86_64", source_kind="qcow2",
         source="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2",
         parent=None, virtual_gb=8,
         build="Official Debian genericcloud qcow2; verified against upstream SHA512SUMS."),
    dict(key="debian-13-base-arm64", name="Debian 13 Minimal arm64 (golden)",
         os_family="debian", os_version="13", arch="aarch64", source_kind="qcow2",
         source="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-arm64.qcow2",
         parent=None, virtual_gb=8,
         build="Official Debian genericcloud qcow2 (arm64)."),
    dict(key="debian-13-iso", name="Debian 13 Installer ISO (immutable asset)",
         os_family="debian", os_version="13", arch="x86_64", source_kind="iso",
         source="https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/",
         parent=None, virtual_gb=1,
         build="Retained installer ISO for clean reference installs; checksum verified."),
    # Role golden images, CoW children of the Debian base (storage-efficient).
    dict(key="debian-13-server", name="Debian 13 Server (golden)", os_family="debian",
         os_version="13", arch="x86_64", source_kind="build", source="",
         parent="debian-13-base", virtual_gb=10,
         build="From debian-13-base: openssh-server, sudo, qemu-guest-agent, cloud-init."),
    dict(key="debian-13-web", name="Debian 13 Web Server (golden)", os_family="debian",
         os_version="13", arch="x86_64", source_kind="build", source="",
         parent="debian-13-server", virtual_gb=12,
         build="From debian-13-server: nginx, php-fpm, application scaffolding."),
    dict(key="debian-13-db", name="Debian 13 Database Server (golden)", os_family="debian",
         os_version="13", arch="x86_64", source_kind="build", source="",
         parent="debian-13-server", virtual_gb=12,
         build="From debian-13-server: postgresql / mariadb."),
    dict(key="debian-13-desktop", name="Debian 13 Desktop (golden)", os_family="debian",
         os_version="13", arch="x86_64", source_kind="build", source="",
         parent="debian-13-base", virtual_gb=16,
         build="From debian-13-base: Xfce desktop + VNC for graphical console labs."),
    dict(key="debian-13-monitoring", name="Debian 13 Monitoring (golden)",
         os_family="debian", os_version="13", arch="x86_64", source_kind="build", source="",
         parent="debian-13-server", virtual_gb=14,
         build="From debian-13-server: log collector + dashboards for defensive labs."),
    # --- Other operating systems (own media/images) ---
    dict(key="kali-base", name="Kali Linux (attacker workstation golden)",
         os_family="kali", os_version="rolling", arch="x86_64", source_kind="qcow2",
         source="https://cdimage.kali.org/current/",
         parent=None, virtual_gb=20,
         build="Official Kali cloud/qcow2 image for the attacker-workstation role."),
    dict(key="ubuntu-2404-base", name="Ubuntu Server 24.04 (golden)", os_family="ubuntu",
         os_version="24.04", arch="x86_64", source_kind="qcow2",
         source="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img",
         parent=None, virtual_gb=10, build="Official Ubuntu cloud image."),
    dict(key="ubuntu-2404-base-arm64", name="Ubuntu Server 24.04 arm64 (golden)", os_family="ubuntu",
         os_version="24.04", arch="aarch64", source_kind="qcow2",
         source="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-arm64.img",
         parent=None, virtual_gb=10, build="Official Ubuntu cloud image (arm64)."),
    dict(key="alpine-base", name="Alpine Linux (minimal golden)", os_family="alpine",
         os_version="3.20", arch="x86_64", source_kind="qcow2",
         source="https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/cloud/nocloud_alpine-3.20.9-x86_64-bios-cloudinit-r0.qcow2",
         parent=None, virtual_gb=2, build="Alpine NoCloud cloud-init image for lightweight targets."),
    dict(key="alpine-base-arm64", name="Alpine Linux arm64 (minimal golden)", os_family="alpine",
         os_version="3.20", arch="aarch64", source_kind="qcow2",
         source="https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/cloud/nocloud_alpine-3.20.9-aarch64-uefi-cloudinit-r0.qcow2",
         parent=None, virtual_gb=2, build="Alpine NoCloud cloud-init image (arm64, UEFI)."),
    dict(key="freebsd-base", name="FreeBSD 14 (golden)", os_family="freebsd",
         os_version="14", arch="x86_64", source_kind="qcow2",
         source="https://download.freebsd.org/releases/VM-IMAGES/",
         parent=None, virtual_gb=10, build="FreeBSD VM image."),
    dict(key="windows-server-base", name="Windows Server (operator-supplied)",
         os_family="windows", os_version="2022", arch="x86_64", source_kind="iso",
         source="", parent=None, virtual_gb=32,
         build="Requires operator-supplied, appropriately licensed evaluation media. "
               "Never downloaded automatically."),
    dict(key="windows-client-base", name="Windows Client (operator-supplied)",
         os_family="windows", os_version="11", arch="x86_64", source_kind="iso",
         source="", parent=None, virtual_gb=32,
         build="Requires operator-supplied, appropriately licensed evaluation media."),
]
