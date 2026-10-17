"""Bootstrap configuration for Pwnforge.

This module holds *bootstrap* configuration only: the handful of values that
must be known before the database is open (data directory, database URL, bind
address, secret key). Everything a user can change at runtime (port, LAN
access, resource limits, theme, ...) lives in the ``settings`` table and is
served through :mod:`backend.app.core.settings_service`.

Values are read, in order of precedence, from:
  1. Environment variables prefixed with ``PWNFORGE_``.
  2. A ``.env`` file in the data directory.
  3. The defaults below.
"""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    env = os.environ.get("PWNFORGE_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".pwnforge").resolve()


class Settings(BaseSettings):
    """Bootstrap settings, immutable for the life of the process."""

    model_config = SettingsConfigDict(
        env_prefix="PWNFORGE_",
        env_file=os.environ.get("PWNFORGE_ENV_FILE", str(_default_data_dir() / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Paths -------------------------------------------------------------
    data_dir: Path = Field(default_factory=_default_data_dir)
    repo_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )

    # --- Server ------------------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 8080
    # A stable secret used to sign sessions. Persisted to the data dir on first
    # run so sessions survive restarts; regenerated only if the file is lost.
    secret_key: str = ""

    # --- Database ----------------------------------------------------------
    database_url: str = ""

    # --- Virtualisation ----------------------------------------------------
    # auto | libvirt | qemu | simulation
    vm_driver: str = "auto"
    libvirt_uri: str = "qemu:///system"

    # --- Behaviour ---------------------------------------------------------
    environment: str = "production"  # production | development | test
    log_level: str = "INFO"

    @property
    def catalog_dir(self) -> Path:
        return self.repo_root / "catalog"

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"

    @property
    def iso_dir(self) -> Path:
        return self.data_dir / "iso"

    @property
    def overlays_dir(self) -> Path:
        return self.data_dir / "overlays"

    @property
    def snapshots_dir(self) -> Path:
        return self.data_dir / "snapshots"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.data_dir / 'pwnforge.db'}"

    def ensure_dirs(self) -> None:
        for p in (
            self.data_dir,
            self.images_dir,
            self.iso_dir,
            self.overlays_dir,
            self.snapshots_dir,
            self.backups_dir,
            self.logs_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)

    def load_or_create_secret(self) -> str:
        """Return a stable secret key, persisting one to the data dir."""
        if self.secret_key:
            return self.secret_key
        secret_file = self.data_dir / "secret_key"
        if secret_file.exists():
            self.secret_key = secret_file.read_text().strip()
            return self.secret_key
        self.data_dir.mkdir(parents=True, exist_ok=True)
        key = secrets.token_urlsafe(48)
        secret_file.write_text(key)
        try:
            secret_file.chmod(0o600)
        except OSError:
            pass
        self.secret_key = key
        return key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    s.load_or_create_secret()
    return s
