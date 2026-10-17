# Installation

Pwnforge targets **Debian** for full virtualisation. It also runs on any host
(macOS, other Linux, CI) using the simulation driver, which is ideal for
development and for using the learning platform without real VMs.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+ and npm (to build the website)
- On a Debian/KVM host, for real VMs:
  ```bash
  sudo apt update
  sudo apt install qemu-system-x86 qemu-utils \
                   libvirt-daemon-system libvirt-clients python3-libvirt \
                   nodejs npm
  sudo adduser "$USER" libvirt
  sudo adduser "$USER" kvm
  # log out/in so the group membership applies
  ```

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
| `PWNFORGE_VM_DRIVER` | `auto` | `auto`/`libvirt`/`qemu`/`simulation` |
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
