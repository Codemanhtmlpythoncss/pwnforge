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
import os
import threading
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings

APP_VERSION = "1.0.0"
UPDATE_SETTING = "admin.update_command"
_BUNDLED_COMMAND = ("bash", "scripts/update.sh")
_TIMEOUT_S = 30 * 60
_UPDATE_LOCK = threading.Lock()


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


def _git_metadata_dir(repo: Path) -> Path | None:
    marker = repo / ".git"
    if marker.is_dir():
        return marker
    if not marker.is_file():
        return None
    try:
        line = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    target = Path(line.partition(":")[2].strip())
    return target if target.is_absolute() else (repo / target).resolve()


def _bundled_update_problem() -> str | None:
    """Explain why the bundled self-updater cannot safely mutate this checkout."""
    repo = _repo_dir()
    git_dir = _git_metadata_dir(repo)
    if git_dir is None or _git("rev-parse", "--show-toplevel") is None:
        return ("This installation is managed by its host and PwnForge cannot access its Git checkout. "
                "Update it from the Nodeyard dashboard's PwnForge page, or ask the host administrator.")

    writable_paths = [repo, git_dir, repo / "frontend"]
    venv = repo / ".venv"
    if venv.exists():
        writable_paths.append(venv)
    if not all(path.is_dir() and os.access(path, os.W_OK) for path in writable_paths):
        return ("This installation is managed by its host and the PwnForge service cannot write the "
                "checkout or its update dependencies. Update it from the Nodeyard dashboard's PwnForge "
                "page, or ask the host administrator.")
    return None


def _update_message(command: str) -> str:
    if not command:
        return ("Updates are managed by the host. Use the Nodeyard dashboard's PwnForge page, "
                "or ask the host administrator to update this installation.")
    try:
        is_bundled = tuple(shlex.split(command)) == _BUNDLED_COMMAND
    except ValueError:
        is_bundled = False
    if is_bundled:
        return _bundled_update_problem() or ""
    # A custom command is an explicit operator choice; it may delegate to a host-level updater.
    return ""


def version_info(session: Session) -> dict:
    """Current version and, when the install is a git checkout, its commit/branch. No network."""
    commit = _git("rev-parse", "--short", "HEAD")
    command = (cfg.get_setting(session, UPDATE_SETTING, "") or "").strip()
    message = _update_message(command)
    return {
        "version": APP_VERSION,
        "commit": commit,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD") if commit else None,
        "update_enabled": bool(command) and not message,
        "update_message": message,
    }


def run_update(session: Session, *, progress=None) -> dict:
    """Run the operator-configured update command. Raises UpdateError when none is set."""
    command = (cfg.get_setting(session, UPDATE_SETTING, "") or "").strip()
    message = _update_message(command)
    if not command or message:
        raise UpdateError(message or "No update command is configured.")
    if not _UPDATE_LOCK.acquire(blocking=False):
        raise UpdateError("Another PwnForge update is already running. Wait for it to finish before retrying.")
    try:
        if progress:
            progress.update(stage="Updating PwnForge", percent=1)
        # The operator chose this command; run it as given (a shell, so pipelines/&& work), in the repo.
        try:
            proc = subprocess.run(command, shell=True, cwd=str(_repo_dir()), capture_output=True,
                                  text=True, timeout=_TIMEOUT_S)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            raise UpdateError(f"The update command timed out after {_TIMEOUT_S // 60} minutes.\n{output[-4000:].strip()}") from exc
        tail = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr.strip() else ""))[-4000:]
        if proc.returncode != 0:
            raise UpdateError(f"The update command failed (exit {proc.returncode}).\n{tail.strip()}")
        try:
            command_name = shlex.split(command)[0]
        except (ValueError, IndexError):
            command_name = "custom updater"
        return {"ok": True, "output": tail.strip(), "command": command_name}
    finally:
        _UPDATE_LOCK.release()


class UpdateError(Exception):
    pass
