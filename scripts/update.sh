#!/usr/bin/env bash
# Update this PwnForge checkout in place: pull, reinstall dependencies, migrate the
# database, rebuild the website, and restart the service when one is managing it.
#
# This is what the in-app Update button runs by default (the admin.update_command
# setting). It only works where the service account may write the checkout and run
# these tools — a personal/dev checkout you run yourself, or a host that grants the
# service the right to restart its unit. On a root-owned install it will stop at the
# first step it isn't allowed to do and say so; update from the host there instead.
set -euo pipefail
cd "$(dirname "$0")/.."
VENV=.venv
say() { printf 'update: %s\n' "$*"; }

say "pulling the latest code"
git pull --ff-only

[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
say "installing Python dependencies"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r backend/requirements.txt
"$VENV/bin/pip" install -q -e . >/dev/null 2>&1 || true

say "applying database migrations"
"$VENV/bin/alembic" upgrade head

# Course text and assessments live in the authored catalogue, so refresh their
# database rows on every update. This touches course content only and preserves
# learner progress, submissions and achievements.
say "refreshing course content"
"$VENV/bin/python" - <<'PY'
from backend.app.catalog.importer import import_courses
from backend.app.database.base import session_scope
with session_scope() as session:
    count = import_courses(session)
print(f"update: refreshed {count} courses")
PY

if command -v npm >/dev/null 2>&1; then
    say "building the website"
    ( cd frontend && { npm ci --no-audit --no-fund --loglevel=error >/dev/null 2>&1 \
        || npm install --no-audit --no-fund --loglevel=error >/dev/null; } && npm run -s build >/dev/null )
else
    say "npm not found; skipping the website build"
fi

say "restarting"
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet pwnforge 2>/dev/null; then
    systemctl restart pwnforge 2>/dev/null \
        || sudo -n systemctl restart pwnforge 2>/dev/null \
        || say "couldn't restart the service automatically — restart PwnForge to finish."
else
    say "no service manager here — restart PwnForge to load the update."
fi
say "done"
