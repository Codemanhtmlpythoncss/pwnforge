"""Reporting PwnForge's version, and applying an update when the operator opts in.

PwnForge runs as an unprivileged service, so it can't update itself (pull the code, reinstall
dependencies, migrate, rebuild, restart the service) on its own. An operator who wants an in-app
update button sets ``admin.update_command`` to a command they trust PwnForge to run for that — for
example a wrapper the host grants through sudo, or the nodeyard dashboard's own updater. The command
is empty by default, and then the button only shows the version and points at the host updater.
"""
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings

APP_VERSION = "1.0.0"
UPDATE_SETTING = "admin.update_command"
_TIMEOUT_S = 30 * 60


def _repo_dir() -> Path:
    # backend/app/core/updater.py -> repo root
    return Path(__file__).resolve().parents[3]


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(_repo_dir()), *args],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def version_info(session: Session) -> dict:
    """Current version and, when the install is a git checkout, its commit/branch. No network."""
    commit = _git("rev-parse", "--short", "HEAD")
    return {
        "version": APP_VERSION,
        "commit": commit,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD") if commit else None,
        "update_enabled": bool((cfg.get_setting(session, UPDATE_SETTING, "") or "").strip()),
    }


def run_update(session: Session, *, progress=None) -> dict:
    """Run the operator-configured update command. Raises UpdateError when none is set."""
    command = (cfg.get_setting(session, UPDATE_SETTING, "") or "").strip()
    if not command:
        raise UpdateError(
            "No in-app updater is configured. Updates are applied by the host "
            "(the nodeyard dashboard's PwnForge page, or re-running the installer), or set "
            f"'{UPDATE_SETTING}' to a command this server may run to update itself.")
    if progress:
        progress.update(stage="Updating PwnForge", percent=1)
    # The operator chose this command; run it as given (a shell, so pipelines/&& work), in the repo.
    proc = subprocess.run(command, shell=True, cwd=str(_repo_dir()), capture_output=True,
                          text=True, timeout=_TIMEOUT_S)
    tail = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr.strip() else ""))[-4000:]
    if proc.returncode != 0:
        raise UpdateError(f"The update command failed (exit {proc.returncode}).\n{tail.strip()}")
    return {"ok": True, "output": tail.strip(), "command": shlex.split(command)[0]}


class UpdateError(Exception):
    pass
