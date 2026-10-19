"""Real machines: the image a host can run, role images, cloud-init seeds, logins, libvirt XML, the console.

No hypervisor is needed: a fake driver that reports real virtualisation on an arm64 host stands in for
libvirt, so the whole start sequence (role image, overlay, seed, IP) runs as it would on a Raspberry Pi."""
from __future__ import annotations

import base64
import os
import stat
import xml.dom.minidom

import pycdlib
import pytest
import yaml

from backend.app.database.models import VMStatus
from backend.app.vms import factory, provision
from backend.app.vms import libvirt_driver as lv
from backend.app.vms.driver import ConsoleInfo, HostCapabilities, VMDriver, VMSpec
from backend.tests.conftest import poll_job


class FakeStream:
    def __init__(self):
        self.sent, self.chunks = [], [b"Debian GNU/Linux 13 web ttyAMA0\r\n\r\nweb login: "]

    def read(self, timeout=1.0):
        return self.chunks.pop(0) if self.chunks else b""

    def write(self, data):
        self.sent.append(data)

    def close(self):
        self.chunks = []


class FakeRealDriver(VMDriver):
    """Behaves like libvirt on an arm64 host, without booting anything."""
    name = "libvirt"

    def __init__(self):
        self.specs, self.builds, self.state, self.stream = {}, [], {}, FakeStream()

    def capabilities(self):
        return HostCapabilities(driver="libvirt", platform="linux", arch="aarch64", cpu_count=4,
                                total_memory_mb=8000, real_virtualization=True, hardware_acceleration=True)

    def create_overlay(self, base_image_path, overlay_path, size_gb):
        assert os.path.exists(base_image_path)
        with open(overlay_path, "w") as f:
            f.write("overlay of " + base_image_path)

    def delete_overlay(self, overlay_path):
        if os.path.exists(overlay_path):
            os.unlink(overlay_path)

    def create_network(self, name, cidr, mode, external):
        return "pwnforge-" + name

    def delete_network(self, ref):
        pass

    def define(self, spec: VMSpec):
        self.specs[spec.name] = spec
        self.state[spec.name] = VMStatus.stopped
        return spec.name

    def start(self, ref):
        self.state[ref] = VMStatus.running

    def stop(self, ref, force=False):
        self.state[ref] = VMStatus.stopped

    def reboot(self, ref):
        pass

    def delete(self, ref):
        self.state.pop(ref, None)

    def status(self, ref):
        return self.state.get(ref, VMStatus.deleted)

    def get_ip(self, ref):
        return "10.200.0.10" if self.state.get(ref) == VMStatus.running else None

    def console(self, ref):
        return ConsoleInfo(kind="serial", host="", port=None)

    def list_domains(self):
        return list(self.state)

    def run_build(self, *, name, arch, disk, seed, ok_marker, fail_marker, timeout_s, log=None):
        ud = _seed_files(seed)["user-data"]
        self.builds.append({"name": name, "arch": arch, "user_data": ud})
        return True, "pwnforge-build: " + ok_marker

    def open_console(self, ref):
        return self.stream


def _seed_files(path) -> dict:
    iso = pycdlib.PyCdlib()
    iso.open(str(path))
    out = {}
    for name in ("user-data", "meta-data"):
        import io
        buf = io.BytesIO()
        iso.get_file_from_iso_fp(buf, rr_path="/" + name)
        out[name] = buf.getvalue().decode()
    assert iso.pvd.volume_identifier.decode().strip() == "cidata"
    iso.close()
    return out


@pytest.fixture
def real(admin, monkeypatch):
    """Swap in the fake real driver, with the arm64 Debian and Alpine images 'downloaded'."""
    from backend.app.core.config import get_settings
    from backend.app.database.base import session_scope
    from backend.app.profiles import service as profiles

    drv = FakeRealDriver()
    monkeypatch.setattr(factory, "select_driver_name", lambda configured="auto": "fake-real")
    factory._cache["fake-real"] = drv
    imgs = get_settings().images_dir
    imgs.mkdir(parents=True, exist_ok=True)
    made = []
    for key in ("debian-13-base-arm64", "alpine-base-arm64"):
        p = imgs / f"{key}.qcow2"
        p.write_bytes(b"QFI\xfb fake cloud image " + key.encode())
        made.append(p)
    from backend.app.database.models import BaseImage
    from backend.app.images import service as images
    with session_scope() as s:
        for key in ("debian-13-base-arm64", "alpine-base-arm64"):
            images.refresh_status(s, s.get(BaseImage, key))      # as after `pwnforge images fetch`
        profiles.recompute_readiness(s)
    yield drv
    factory._cache.pop("fake-real", None)
    monkeypatch.undo()
    for p in made:
        p.unlink(missing_ok=True)
    with session_scope() as s:
        for key in ("debian-13-base-arm64", "alpine-base-arm64"):
            images.refresh_status(s, s.get(BaseImage, key))
        profiles.recompute_readiness(s)


# ---- which image this host runs --------------------------------------------------------------------
def test_linux_profiles_run_on_the_distros_image_for_this_cpu(admin):
    from backend.app.database.base import session_scope
    with session_scope() as s:
        assert provision.host_image(s, "debian-13-web", "aarch64").key == "debian-13-base-arm64"
        assert provision.host_image(s, "debian-13-web", "arm64").key == "debian-13-base-arm64"
        assert provision.host_image(s, "debian-13-web", "x86_64").key == "debian-13-base"
        assert provision.host_image(s, "ubuntu-2404-base", "aarch64").key == "ubuntu-2404-base-arm64"
        assert provision.host_image(s, "alpine-base", "aarch64").key == "alpine-base-arm64"
        assert provision.host_image(s, "windows-server-base", "aarch64") is None
        assert provision.host_image(s, "windows-server-base", "x86_64") is None     # install media, not an image
        assert provision.host_image(s, "no-such-image", "x86_64") is None


def test_readiness_follows_the_image_this_host_runs(real):
    from backend.app.database.base import session_scope
    from backend.app.database.models import ProfileReadiness, VMProfile
    with session_scope() as s:
        assert s.get(VMProfile, "linux-enum-ssh-linux-e").readiness == ProfileReadiness.ready
        assert s.get(VMProfile, "container-sec-ubuntu-srv-a").readiness == ProfileReadiness.requires_base_image
        assert s.get(VMProfile, "ad-identity-windows-srv-a").readiness == ProfileReadiness.requires_install_media


# ---- logins, cloud-init and seeds ------------------------------------------------------------------
def test_login_passwords_are_derived_per_machine():
    a, b = provision.login_password("vm-a"), provision.login_password("vm-b")
    assert a == provision.login_password("vm-a") and a != b and len(a) == 14
    assert not set(a) & set("0O1lI")
    assert provision.hostname_for("1a2b3c4d-web") == "web"
    assert provision.hostname_for("x-Target_1!") == "target-1"


def test_instance_user_data_makes_the_learner_account():
    ud = provision.instance_user_data("web", "Secr3tPass", "debian")
    assert ud.startswith("#cloud-config\n")
    doc = yaml.safe_load(ud)
    user = doc["users"][0]
    assert doc["hostname"] == "web" and user["name"] == "learner" and user["plain_text_passwd"] == "Secr3tPass"
    assert user["lock_passwd"] is False and "sudo" in user["groups"] and doc["ssh_pwauth"] is True
    assert yaml.safe_load(provision.instance_user_data("t", "p", "alpine"))["users"][0]["groups"] == ["wheel"]


def test_build_script_only_passes_package_and_unit_names_to_the_shell():
    sh = provision.build_script("debian", ["nginx", "admin-panel", "x; rm -rf /", "$(id)"], ["nginx", "a b"])
    assert "for p in admin-panel nginx; do" in sh and "rm -rf /" not in sh and "$(id)" not in sh
    assert "for s in nginx; do" in sh
    assert provision.BUILD_OK in sh and provision.BUILD_FAILED in sh and "truncate -s 0 /etc/machine-id" in sh
    doc = yaml.safe_load(provision.build_user_data("debian", ["nginx"], ["nginx"]))
    script = base64.b64decode(doc["write_files"][0]["content"]).decode()
    assert "for p in nginx; do" in script and doc["power_state"]["mode"] == "poweroff"
    assert "apk add" in provision.build_script("alpine", ["openssh"], ["sshd"])


def test_seed_is_a_private_cidata_disk(tmp_path):
    p = provision.write_seed(tmp_path / "s.iso", "#cloud-config\nhostname: web\n", "instance-id: i-1\n")
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    files = _seed_files(p)
    assert files["user-data"].startswith("#cloud-config") and files["meta-data"] == "instance-id: i-1\n"


# ---- libvirt definitions -----------------------------------------------------------------------------
def test_arm64_domains_use_uefi_on_the_virt_machine():
    x = lv.domain_xml(VMSpec(name="pwnforge-a", vcpu=1, memory_mb=1024, arch="arm64", overlay_path="/o.qcow2",
                             cloud_init_iso="/s.iso", network_ref="pwnforge-n"))
    dom = xml.dom.minidom.parseString(x)
    os_el = dom.getElementsByTagName("os")[0]
    assert os_el.getAttribute("firmware") == "efi"
    assert dom.getElementsByTagName("type")[0].getAttribute("machine") == "virt"
    assert dom.getElementsByTagName("gic") and not dom.getElementsByTagName("apic")
    disks = dom.getElementsByTagName("disk")
    assert len(disks) == 2 and disks[1].getElementsByTagName("readonly")       # the seed, read-only
    assert not dom.getElementsByTagName("graphics")                             # headless: serial console only


def test_x86_domains_and_networks():
    dom = xml.dom.minidom.parseString(lv.domain_xml(VMSpec(name="a", vcpu=2, memory_mb=512, arch="x86_64",
                                                             overlay_path="/o", headless=False)))
    assert dom.getElementsByTagName("type")[0].getAttribute("machine") == "q35"
    assert dom.getElementsByTagName("graphics")[0].getAttribute("listen") == "127.0.0.1"
    iso = xml.dom.minidom.parseString(lv.network_xml("pwnforge-1a2b3c4d-lab", "10.200.3.0/24"))
    assert not iso.getElementsByTagName("forward")                              # isolated: no route out
    assert xml.dom.minidom.parseString(lv.network_xml("pwnforge-build", "10.254.254.0/24", nat=True)) \
        .getElementsByTagName("forward")[0].getAttribute("mode") == "nat"
    names = {lv.bridge_name(f"pwnforge-1a2b3c4d-{n}") for n in ("lab", "dmz", "corp")}
    assert len(names) == 3 and all(len(n) <= 15 for n in names)                 # unique, and valid Linux names


# ---- role images ------------------------------------------------------------------------------------
def test_role_images_are_built_once_and_failures_leave_nothing(real, tmp_path):
    from backend.app.database.base import session_scope
    from backend.app.database.models import BaseImage
    from backend.app.images import service as images
    with session_scope() as s:
        img = s.get(BaseImage, "debian-13-base-arm64")
        path = images.image_path(img)
        kw = dict(os_family="debian", packages=["nginx", "php-fpm"], services=["nginx"], arch="aarch64", disk_gb=8)
        first = provision.role_image(real, img, path, **kw)
        again = provision.role_image(real, img, path, **kw)
        assert first == again and first.exists() and len(real.builds) == 1
        assert "nginx" in base64.b64decode(yaml.safe_load(real.builds[0]["user_data"])["write_files"][0]["content"]).decode()

        real.run_build = lambda **k: (False, "E: Unable to locate package nginx")
        with pytest.raises(provision.ProvisionError) as e:
            provision.role_image(real, img, path, **dict(kw, packages=["something-else"]))
        assert "Unable to locate" in str(e.value)
        assert not list(provision.roles_dir().glob("*.building.qcow2")) and not list(provision.roles_dir().glob("*.seed.iso"))


# ---- a whole lab, end to end -------------------------------------------------------------------------
def test_start_lab_boots_real_machines_with_a_login(real, admin):
    r = admin.post("/api/lab-instances", json={"lab_id": "linux-practice-basic"})
    assert r.status_code == 200, r.text
    job = poll_job(admin, r.json()["job_id"])
    assert job["status"] == "succeeded", job
    li = next(x for x in admin.get("/api/lab-instances").json()["items"] if x["id"] == r.json()["lab_instance_id"])
    m = li["machines"][0]
    assert m["status"] == "running" and not m["simulated"] and m["ip_address"] == "10.200.0.10"
    assert m["login"] == {"username": "learner", "password": provision.login_password(m["id"])}

    spec = real.specs[f"pwnforge-{m['id']}"]
    assert spec.arch == "aarch64" and spec.network_ref.startswith("pwnforge-")
    seed = _seed_files(spec.cloud_init_iso)
    assert m["login"]["password"] in seed["user-data"] and "hostname: \"host\"" in seed["user-data"]
    assert f"instance-id: {m['id']}" in seed["meta-data"]
    assert "for p in openssh-server sudo; do" in base64.b64decode(
        yaml.safe_load(real.builds[-1]["user_data"])["write_files"][0]["content"]).decode()

    # the serial console, for the owner only, and not from another site
    with admin.websocket_connect(f"/api/ws/console/{m['id']}") as ws:
        assert "serial console" in ws.receive_text()
        assert b"login:" in ws.receive_bytes()
        ws.send_text("learner\r")
    assert b"learner\r" in real.stream.sent
    with admin.websocket_connect(f"/api/ws/console/{m['id']}", headers={"origin": "https://evil.example"}) as ws:
        with pytest.raises(Exception):
            ws.receive_text()

    seed_path = spec.cloud_init_iso
    assert admin.delete(f"/api/lab-instances/{li['id']}").status_code == 200
    assert not os.path.exists(seed_path)


def test_windows_labs_are_refused_on_an_arm64_host_with_a_reason(real, admin):
    r = admin.post("/api/lab-instances", json={"lab_id": "enterprise-identity-lab"})
    job = poll_job(admin, r.json()["job_id"])
    assert job["status"] == "failed" and "aarch64" in job["error"]
