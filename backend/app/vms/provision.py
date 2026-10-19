"""Turning a VM profile into a bootable machine on a real hypervisor.

Three pieces, used only by drivers that boot real guests (libvirt):

  * the base image for THIS host: a profile names a golden image (often an x86_64
    role image such as ``debian-13-web``); on an arm64 host the same Linux distro's
    arm64 cloud image is used instead, because the profile's packages come from the
    distro and exist for both. Operating systems with no image for the host's CPU
    (Windows on an arm64 host) are refused with a clear reason.
  * the role image: the base plus the profile's packages and services, built once
    per (base, packages, services) by booting the base on a temporary NAT network
    with cloud-init, then kept and reused as the parent of every overlay. Lab
    networks themselves stay isolated; only this build step reaches the internet,
    and only for the distro's package mirrors.
  * the per-machine cloud-init seed: hostname, and a ``learner`` account whose
    password is derived from the server's secret key and the machine's id (so it
    is never stored, and only the machine's owner is shown it).
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import hmac
import io
import json
import os
import re
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.database.models import BaseImage

LOGIN_USER = "learner"
BUILD_OK = "PWNFORGE-BUILD-OK"
BUILD_FAILED = "PWNFORGE-BUILD-FAILED"
RECIPE_VERSION = 1              # bump to rebuild every role image (e.g. the build steps changed)
BUILD_TIMEOUT_S = 40 * 60       # a slow SD card and mirror can take a while the first time
_ALIASES = {"x86_64": "x86_64", "amd64": "x86_64", "aarch64": "aarch64", "arm64": "aarch64"}
_PW_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # no 0/O, 1/l/I


class ProvisionError(Exception):
    pass


def norm_arch(arch: str) -> str:
    return _ALIASES.get((arch or "").lower(), (arch or "").lower())


# ---- which base image this host runs ------------------------------------------------------------
def host_image_from(images: dict, key: str | None, host_arch: str):
    """The downloadable base image that stands in for image ``key`` on a host with ``host_arch``.

    ``images`` maps keys to image records. Walks ``key`` up to its root image (a role image's parents),
    then picks the root itself or, for another CPU, the same distro and version's image for this one."""
    img, seen = images.get(key) if key else None, set()
    while img is not None and img.parent_key and img.key not in seen:
        seen.add(img.key)
        img = images.get(img.parent_key)
    if img is None:
        return None
    want = norm_arch(host_arch)
    if norm_arch(img.arch) == want and img.source_kind == "qcow2":
        return img
    for other in sorted(images.values(), key=lambda i: i.key):
        if (other.os_family == img.os_family and other.os_version == img.os_version and not other.parent_key
                and other.source_kind == "qcow2" and norm_arch(other.arch) == want):
            return other
    return None


def host_image(session: Session, key: str | None, host_arch: str) -> BaseImage | None:
    return host_image_from({i.key: i for i in session.execute(select(BaseImage)).scalars()}, key, host_arch)


# ---- login --------------------------------------------------------------------------------------
def login_password(vm_id: str) -> str:
    """The learner account's password for one machine: derived, never stored."""
    key = get_settings().load_or_create_secret().encode()
    digest = hmac.new(key, b"pwnforge-vm-login:" + vm_id.encode(), hashlib.sha256).digest()
    return "".join(_PW_ALPHABET[b % len(_PW_ALPHABET)] for b in digest[:14])


def derive_flag(instance_id: str) -> str:
    """A lab instance's flag: PWN{...}, derived from the server secret and the instance id. Unguessable and
    unique per instance, never stored — the same value is planted in the target and re-derived to validate a
    submission, so you have to actually read it off the box."""
    key = get_settings().load_or_create_secret().encode()
    digest = hmac.new(key, b"pwnforge-flag:" + instance_id.encode(), hashlib.sha256).hexdigest()
    return "PWN{" + digest[:24] + "}"


def _safe_login(user: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "", (user or "user").lower())[:32] or "user"


def target_user_data(hostname: str, os_family: str, user: str, password: str, flag: str, sudo: bool = False) -> str:
    """A black-box target: an account whose (weak) password the learner must DISCOVER — it is never shown — with
    the flag planted in that account's home. No learner login is created; getting in is the whole challenge."""
    safe = _safe_login(user)
    shell = "/bin/ash" if os_family == "alpine" else "/bin/bash"
    home = "/root" if safe == "root" else "/home/" + safe
    lines = [
        "#cloud-config",
        f"hostname: {_yaml_str(hostname)}",
        "manage_etc_hosts: true",
        "users:",
        f"  - name: {safe}",
        f"    shell: {shell}",
        "    lock_passwd: false",
        f"    plain_text_passwd: {_yaml_str(password)}",
    ]
    if sudo:
        lines += [f"    groups: [{'wheel' if os_family == 'alpine' else 'sudo'}]", "    sudo: \"ALL=(ALL) ALL\""]
    plant = "mkdir -p %s && printf '%%s\\n' %s > %s/flag.txt && chown %s:%s %s/flag.txt && chmod 600 %s/flag.txt" % (
        home, _sh_quote(flag), home, safe, safe, home, home)
    lines += [
        "ssh_pwauth: true",
        "disable_root: true" if safe != "root" else "disable_root: false",
        "runcmd:",
        f"  - [sh, -c, {_yaml_str(plant)}]",
        "",
    ]
    return "\n".join(lines)


def _sh_quote(s: str) -> str:
    return "'" + str(s).replace("'", "'\\''") + "'"


def hostname_for(name: str) -> str:
    """A valid hostname from a machine name like ``1a2b3c4d-web``: the role part."""
    part = name.split("-", 1)[1] if "-" in name else name
    h = re.sub(r"[^a-z0-9-]+", "-", part.lower()).strip("-")[:63]
    return h or "lab"


# ---- cloud-init ---------------------------------------------------------------------------------
def _yaml_str(s: str) -> str:
    return json.dumps(s)   # a JSON string is a valid YAML scalar


def instance_user_data(hostname: str, password: str, os_family: str, flag: str | None = None) -> str:
    admin_group = "wheel" if os_family == "alpine" else "sudo"
    lines = [
        "#cloud-config",
        f"hostname: {_yaml_str(hostname)}",
        "manage_etc_hosts: true",
        "users:",
        f"  - name: {LOGIN_USER}",
        "    gecos: PwnForge learner",
        "    shell: /bin/bash" if os_family != "alpine" else "    shell: /bin/ash",
        f"    groups: [{admin_group}]",
        "    sudo: \"ALL=(ALL) ALL\"",
        "    lock_passwd: false",
        f"    plain_text_passwd: {_yaml_str(password)}",
        "ssh_pwauth: true",
        "disable_root: true",
    ]
    if flag:
        # The challenge flag, planted in the learner's home so there's something real to find and submit.
        home = "/home/" + LOGIN_USER
        plant = "mkdir -p %s && printf '%%s\\n' %s > %s/flag.txt && chown %s:%s %s/flag.txt && chmod 600 %s/flag.txt" % (
            home, _sh_quote(flag), home, LOGIN_USER, LOGIN_USER, home, home)
        lines += ["runcmd:", f"  - [sh, -c, {_yaml_str(plant)}]"]
    lines.append("")
    return "\n".join(lines)


_BUILD_SCRIPT_APT = """#!/bin/sh
# PwnForge: prepare a role image. Real packages are installed; names that aren't packages
# (a profile's own app components) are skipped with a note on the console.
export DEBIAN_FRONTEND=noninteractive
log() { echo "pwnforge-build: $*" | tee /dev/console; }
ok=1
apt-get update || ok=0
want=""
for p in @PKGS@; do
  if apt-cache show "$p" >/dev/null 2>&1; then want="$want $p"; else log "skipping $p (not a package here)"; fi
done
apt-get install -y --no-install-recommends qemu-guest-agent $want || ok=0
for p in $want; do dpkg -s "$p" >/dev/null 2>&1 || { log "missing $p"; ok=0; }; done
for s in @SVCS@; do systemctl enable "$s" >/dev/null 2>&1 || log "no service called $s"; done
apt-get clean
truncate -s 0 /etc/machine-id; rm -f /var/lib/dbus/machine-id
if [ "$ok" = 1 ]; then log @OK@; else log @FAILED@; fi
"""

_BUILD_SCRIPT_APK = """#!/bin/sh
# PwnForge: prepare a role image (Alpine).
log() { echo "pwnforge-build: $*" | tee /dev/console; }
ok=1
apk update || ok=0
apk add qemu-guest-agent >/dev/null 2>&1 || log "no qemu-guest-agent"
for p in @PKGS@; do apk add "$p" >/dev/null 2>&1 || log "skipping $p (not a package here)"; done
for s in @SVCS@; do rc-update add "$s" default >/dev/null 2>&1 || log "no service called $s"; done
if [ "$ok" = 1 ]; then log @OK@; else log @FAILED@; fi
"""


def build_script(os_family: str, packages: list[str], services: list[str]) -> str:
    safe = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]*$")      # package and unit names only: nothing else reaches the shell
    pkgs = " ".join(sorted({p for p in packages if safe.match(p)}))
    svcs = " ".join(sorted({s for s in services if safe.match(s)}))
    tpl = _BUILD_SCRIPT_APK if os_family == "alpine" else _BUILD_SCRIPT_APT
    return (tpl.replace("@PKGS@", pkgs).replace("@SVCS@", svcs)
            .replace("@OK@", BUILD_OK).replace("@FAILED@", BUILD_FAILED))


def build_user_data(os_family: str, packages: list[str], services: list[str]) -> str:
    """Run the build script, report the result on the console, power off."""
    script = base64.b64encode(build_script(os_family, packages, services).encode()).decode()
    return "\n".join([
        "#cloud-config",
        "hostname: pwnforge-build",
        "write_files:",
        "  - path: /root/pwnforge-build.sh",
        "    permissions: \"0700\"",
        "    encoding: b64",
        f"    content: {script}",
        "runcmd:",
        "  - [sh, /root/pwnforge-build.sh]",
        "power_state:",
        "  mode: poweroff",
        "  delay: now",
        "  condition: true",
        "",
    ])


def meta_data(instance_id: str, hostname: str) -> str:
    return f"instance-id: {instance_id}\nlocal-hostname: {hostname}\n"


def write_seed(path: Path, user_data: str, meta: str) -> Path:
    """A NoCloud seed disk (ISO 9660 labelled ``cidata``), readable only by its owner."""
    import pycdlib

    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, rock_ridge="1.09", vol_ident="cidata")
    for name, text in (("user-data", user_data), ("meta-data", meta)):
        data = text.encode()
        iso.add_fp(io.BytesIO(data), len(data), "/" + name.replace("-", "").upper() + ".;1",
                   rr_name=name, joliet_path="/" + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    iso.write(str(tmp))
    iso.close()
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


# ---- role images --------------------------------------------------------------------------------
def roles_dir() -> Path:
    return get_settings().images_dir / "roles"


def role_key(base: BaseImage, base_path: Path, os_family: str, packages: list[str], services: list[str]) -> str:
    st = base_path.stat()
    blob = json.dumps({"v": RECIPE_VERSION, "base": base.key, "size": st.st_size, "mtime": int(st.st_mtime),
                       "os": os_family, "packages": sorted(set(packages)), "services": sorted(set(services))},
                      sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:20]


def role_image(driver, base: BaseImage, base_path: Path, *, os_family: str, packages: list[str],
               services: list[str], arch: str, disk_gb: int, log=None) -> Path:
    """The role image for these packages and services, built the first time it's needed."""
    log = log or (lambda msg: None)
    key = role_key(base, base_path, os_family, packages, services)
    d = roles_dir()
    d.mkdir(parents=True, exist_ok=True)
    final, done = d / f"{key}.qcow2", d / f"{key}.ok"
    if final.exists() and done.exists():
        return final
    with open(d / f"{key}.lock", "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)           # one build per role at a time; others wait for it
        if final.exists() and done.exists():
            return final
        work, seed = d / f"{key}.building.qcow2", d / f"{key}.seed.iso"
        for p in (work, seed, final):
            p.unlink(missing_ok=True)
        driver.create_overlay(str(base_path), str(work), max(disk_gb, 10))
        write_seed(seed, build_user_data(os_family, packages, services), meta_data(f"build-{key}", "pwnforge-build"))
        log("Preparing the machine image (first time only: installing " + (", ".join(sorted(set(packages))) or "updates") + ")")
        try:
            ok, tail = driver.run_build(name=f"pwnforge-build-{key[:12]}", arch=arch, disk=str(work), seed=str(seed),
                                        ok_marker=BUILD_OK, fail_marker=BUILD_FAILED, timeout_s=BUILD_TIMEOUT_S, log=log)
        finally:
            seed.unlink(missing_ok=True)
        if not ok:
            work.unlink(missing_ok=True)
            raise ProvisionError("Couldn't prepare the machine image (packages: %s). Last console lines:\n%s"
                                 % (", ".join(sorted(set(packages))) or "none", tail[-1500:]))
        os.chmod(work, 0o644)
        os.replace(work, final)
        done.write_text(json.dumps({"base": base.key, "packages": sorted(set(packages)),
                                    "services": sorted(set(services)), "built": int(time.time())}))
        return final
