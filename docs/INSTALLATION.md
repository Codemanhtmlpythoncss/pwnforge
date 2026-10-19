# Installation

PwnForge's learning website can run on any host. Real lab guests require Linux,
QEMU, and libvirt. KVM accelerates guests when available; without `/dev/kvm`,
QEMU TCG still boots real guest operating systems but runs substantially slower.
PwnForge does not create pretend VMs in production.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+ and npm (to build the website)
- On a Debian/Linux host, for real VMs:
  ```bash
  sudo apt update
  sudo apt install qemu-system-x86 qemu-utils \
                   libvirt-daemon-system libvirt-clients python3-libvirt \
                   nodejs npm
  sudo adduser "$USER" libvirt
  sudo adduser "$USER" kvm  # only needed when /dev/kvm is available
  # log out/in so the group membership applies
  ```
- On an **arm64** host (a Raspberry Pi 4/5 with 64-bit Raspberry Pi OS or Debian, an
  arm64 server), use `qemu-system-arm qemu-efi-aarch64` instead of `qemu-system-x86`.

## Real lab machines

With QEMU, libvirt and the `libvirt` Python binding available, "Start lab" boots
real virtual machines (the `libvirt` driver is picked automatically). With no
KVM device, libvirt runs the guests through QEMU TCG software emulation instead:
they remain real VMs, but boot and runtime are slower.

- **Images.** Fetch the cloud images for your CPU once, for example on arm64:
  `pwnforge images fetch debian-13-base-arm64` (also `alpine-base-arm64` and
  `ubuntu-2404-base-arm64`; on x86_64 the same names without `-arm64`). A Linux
  lab machine runs on its distribution's image for the host's CPU, so x86_64 lab
  profiles run unchanged on a Raspberry Pi. Windows machines need an x86_64 host.
- **Machine images.** The first start of each kind of machine boots its image on a
  temporary NAT network, installs that machine's packages with cloud-init, and
  keeps the result in `<data>/images/roles/`. That takes a few minutes and needs the
  internet once; later starts take seconds. Lab networks themselves stay isolated.
- **Logging in.** Each machine gets a `learner` account (with sudo) whose password
  is shown to its owner on the lab page; the terminal there is the machine's real
  serial console.
- **Permissions.** libvirt's QEMU user must be able to reach the disks: give the
  data directory and its `images/` and `overlays/` folders mode `0751`.
- **The Python binding.** Install `python3-libvirt` and link it into the venv
  (both come from the same `python3`):
  `ln -s /usr/lib/python3/dist-packages/libvirt*.py /usr/lib/python3/dist-packages/libvirtmod*.so .venv/lib/python3.*/site-packages/`

## Guided install (Debian)

```bash
cd pwnforge
bash scripts/install/install.sh
```

The installer: detects the host and virtualisation support; checks RAM/disk;
creates a venv and installs dependencies; creates the data directory; runs
`alembic upgrade head`; imports the catalogue; builds the frontend; creates the
first admin (interactively) if none exists; and runs `pwnforge doctor`. It is
**safe to re-run** — it never overwrites an existing database or admin.

> It downloads **no** OS images. Fetch base images later, explicitly, with
> `pwnforge images fetch <key>`.

## Manual install (any host)

```bash
cd pwnforge
python3 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e .                         # installs the `pwnforge` command
alembic upgrade head                     # or: python -c "from backend.app.database.init_db import initialise; initialise()"
pwnforge init                             # imports catalogue, creates admin
(cd frontend && npm install && npm run build)
pwnforge serve
```

Open `http://localhost:8080`.

## Configuration

Bootstrap config comes from `PWNFORGE_*` environment variables (or a `.env` in
the data directory). Key ones:

| Variable | Default | Meaning |
|----------|---------|---------|
| `PWNFORGE_DATA_DIR` | `~/.pwnforge` | Where DB, images, overlays, backups live |
| `PWNFORGE_DATABASE_URL` | `sqlite:///<data>/pwnforge.db` | DB URL (Postgres supported) |
| `PWNFORGE_VM_DRIVER` | `auto` | `auto`/`libvirt`/`qemu`; simulation is test-only |
| `PWNFORGE_LIBVIRT_URI` | `qemu:///system` | libvirt connection |

Everything else (port, LAN access, RAM/CPU limits, cleanup, theme, …) is a
**runtime** setting changed in Admin → Settings or via `PUT /api/settings/{key}`.

## systemd

See `deploy/systemd/pwnforge.service`:

```bash
sudo cp deploy/systemd/pwnforge.service /etc/systemd/system/
# edit User=, WorkingDirectory=, Environment= to match your install
sudo systemctl daemon-reload
sudo systemctl enable --now pwnforge
```

Run as a dedicated non-root user in the `libvirt` and `kvm` groups. Restarting
the service does not stop running VMs (libvirtd manages those); on start
Pwnforge reconciles its database with the hypervisor.

## Upgrading

```bash
git pull           # or copy the new release over
. .venv/bin/activate
pip install -r backend/requirements.txt
alembic upgrade head
pwnforge init       # re-imports catalogue; preserves users, progress, achievements
(cd frontend && npm install && npm run build)
sudo systemctl restart pwnforge
```

## Uninstall

Remove the service and the code. Your VM data and database in
`PWNFORGE_DATA_DIR` are **left in place** unless you delete that directory
yourself.
