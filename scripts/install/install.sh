#!/usr/bin/env bash
#
# Pwnforge installer for Debian hosts.
#
# Safe to re-run: it never overwrites an existing database or admin account.
# It does NOT download any OS images — base images are fetched later, only when
# you explicitly run `pwnforge images fetch <key>`.
#
set -euo pipefail

PWNFORGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA_DIR="${PWNFORGE_DATA_DIR:-$HOME/.pwnforge}"
PYTHON="${PYTHON:-python3}"

say() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

say "Pwnforge installer"
say "Repo:   $PWNFORGE_ROOT"
say "Data:   $DATA_DIR"

# 1. Detect host
OS="$(uname -s)"; ARCH="$(uname -m)"
say "Host: $OS / $ARCH"
if [ "$OS" != "Linux" ]; then
  warn "Non-Linux host: real KVM virtualisation is unavailable; the platform"
  warn "will run with the simulation driver (no real guests). Deploy on Debian"
  warn "for full virtualisation."
fi

# 2. Virtualisation support (informational)
if [ -e /dev/kvm ]; then say "KVM present (/dev/kvm)"; else warn "No /dev/kvm — install qemu-kvm / check BIOS virtualisation."; fi
command -v qemu-img >/dev/null 2>&1 || warn "qemu-img not found (apt install qemu-utils)."
command -v virsh    >/dev/null 2>&1 || warn "virsh not found (apt install libvirt-clients libvirt-daemon-system)."

# 3. Resource check
if command -v free >/dev/null 2>&1; then say "Memory: $(free -h | awk '/Mem:/{print $2" total, "$7" available"}')"; fi
say "Disk: $(df -h "$HOME" | awk 'NR==2{print $4" free"}')"

# 4. Python venv + deps
cd "$PWNFORGE_ROOT"
if [ ! -d .venv ]; then say "Creating virtualenv"; "$PYTHON" -m venv .venv; fi
# shellcheck disable=SC1091
. .venv/bin/activate
say "Installing Python dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r backend/requirements.txt
if [ "$OS" = "Linux" ] && [ -e /dev/kvm ]; then
  pip install --quiet libvirt-python || warn "libvirt-python failed; use the distro package python3-libvirt."
fi

# 5. Directories
mkdir -p "$DATA_DIR"/{images,iso,overlays,snapshots,backups,logs}

# 6. Database migrations
export PWNFORGE_DATA_DIR="$DATA_DIR"
say "Applying database migrations"
alembic upgrade head

# 7. Seed catalogue (idempotent) without creating an admin yet
say "Importing catalogue (60+ courses, 1000+ profiles)"
python - <<'PY'
from backend.app.database.init_db import seed
counts = seed(include_profiles=True)
print("  imported:", counts)
PY

# 8. Build frontend if Node is available
if command -v npm >/dev/null 2>&1; then
  say "Building frontend"
  (cd frontend && npm install --no-audit --no-fund >/dev/null 2>&1 && npm run build >/dev/null 2>&1) \
    && say "Frontend built (frontend/dist)" || warn "Frontend build failed; API still runs."
else
  warn "npm not found; skipping frontend build. The API will serve a placeholder."
fi

# 9. Create admin if none exists
if python -c "from backend.app.auth.service import count_users_safe; import sys; sys.exit(0 if count_users_safe() else 1)"; then
  say "An administrator already exists; not creating another."
else
  say "Create the first administrator account:"
  read -r -p "  Username: " ADMIN_USER
  python -m backend.app.cli init --admin-user "$ADMIN_USER" --profiles
fi

# 10. Health check
say "Running diagnostics"
python -m backend.app.cli doctor || warn "doctor reported problems (often just missing base images on a fresh host)."

say "Done. Start the server with:"
echo "    cd $PWNFORGE_ROOT && . .venv/bin/activate && pwnforge serve"
echo "Then open: http://localhost:8080"
echo "To install as a systemd service, see deploy/systemd/pwnforge.service and docs/INSTALLATION.md."
