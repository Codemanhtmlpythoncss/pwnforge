"""Runtime settings: a typed, DB-backed registry.

Each entry declares a default, type, category and description. The admin API
exposes these; consumers read them through :func:`get_setting`. There are no
decorative settings — each key is read by a concrete subsystem (noted in the
description) so changing it has a real effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Setting


@dataclass(frozen=True)
class SettingDef:
    key: str
    default: Any
    value_type: str
    category: str
    description: str


DEFAULTS: list[SettingDef] = [
    # --- server / access ---
    SettingDef("server.port", 8080, "int", "server",
               "HTTP port the website binds to (read by the serve command)."),
    SettingDef("server.lan_access", False, "bool", "server",
               "If true, bind 0.0.0.0 so LAN and VPN clients can reach the site. Restart PwnForge after changing; never port-forward the web port to the internet."),
    SettingDef("server.allowed_origins", [], "list", "server",
               "Extra CORS origins permitted (LAN URLs). localhost is always allowed."),
    SettingDef("auth.session_ttl_hours", 168, "int", "auth",
               "Session lifetime in hours before re-login is required."),
    SettingDef("auth.registration_open", False, "bool", "auth",
               "Allow self-service learner registration."),
    SettingDef("admin.update_command", "bash scripts/update.sh", "string", "maintenance",
               "Command the in-app Update button runs to update PwnForge (pull, reinstall, migrate, "
               "rebuild, restart). The bundled updater needs a writable Git checkout and dependencies; "
               "root-managed installs should use their host updater. A custom command may delegate to "
               "a host updater; clear this setting to disable the button."),
    SettingDef("auth.min_password_length", 1, "int", "auth",
               "Minimum password length enforced on create/change (1: any password that isn't empty)."),
    # --- resource limits (consumed by the VM capacity planner) ---
    SettingDef("vm.storage_dir", "", "string", "resources",
               "Override directory for VM overlays/images (blank = data dir default)."),
    SettingDef("vm.max_total_vcpu", 8, "int", "resources",
               "Max vCPUs committed across running VMs (capacity planner)."),
    SettingDef("vm.max_total_memory_mb", 8192, "int", "resources",
               "Max RAM (MB) committed across running VMs. User-configurable."),
    SettingDef("vm.ram_overcommit_ratio", 1.0, "float", "resources",
               "Allowed RAM overcommit multiplier (1.0 = no overcommit)."),
    SettingDef("vm.max_concurrent", 4, "int", "resources",
               "Maximum number of simultaneously running VM instances."),
    SettingDef("vm.default_vcpu", 1, "int", "resources",
               "Default vCPUs for a VM when a profile omits it."),
    SettingDef("vm.default_memory_mb", 1024, "int", "resources",
               "Default RAM (MB) for a VM when a profile omits it."),
    SettingDef("vm.per_user_memory_mb", 0, "int", "resources",
               "Optional per-user RAM budget (MB). 0 (default) disables the per-user cap."),
    SettingDef("vm.reserve_host_memory_mb", 2048, "int", "resources",
               "RAM (MB) kept free for the host; never scheduled to VMs."),
    # --- lifecycle / cleanup ---
    SettingDef("vm.auto_shutdown_minutes", 120, "int", "lifecycle",
               "Idle minutes before a disposable VM is auto-stopped (0 = never)."),
    SettingDef("vm.idle_timeout_minutes", 30, "int", "lifecycle",
               "Minutes without console/terminal activity counted as idle."),
    SettingDef("storage.image_cache_gb", 40, "int", "storage",
               "Soft cap for cached base images; prune suggestions above this."),
    SettingDef("storage.snapshot_retention", 5, "int", "storage",
               "Max snapshots kept per VM before the oldest is a prune candidate."),
    SettingDef("storage.cleanup_policy", "manual", "string", "storage",
               "manual | on_stop | scheduled — governs overlay garbage collection."),
    SettingDef("storage.low_space_warn_gb", 10, "int", "storage",
               "Free-space threshold (GB) that raises a dashboard warning."),
    # --- networking ---
    SettingDef("network.default_mode", "isolated", "string", "network",
               "Default virtual network mode for new labs (isolated recommended)."),
    SettingDef("network.allow_external", False, "bool", "network",
               "Permit labs to request NAT/external connectivity (requires confirm)."),
    SettingDef("network.base_cidr", "10.200.0.0/16", "string", "network",
               "Supernet from which per-lab subnets are carved."),
    # --- remote access (backend/app/remote) ---
    SettingDef("remote.host_address", "", "string", "remote",
               "Private address clients use to reach this host (VPN/Tailscale/LAN name). Blank = detected."),
    SettingDef("remote.jump_user", "pwnforge-jump", "string", "remote",
               "No-shell SSH account used as a jump host into the lab networks (see Remote access)."),
    SettingDef("remote.ssh_port", 22, "int", "remote",
               "SSH port of this host, used in the jump-host commands shown to users."),
    SettingDef("vpn.enabled", False, "bool", "remote",
               "Turn on after OpenVPN is installed and reachable: shows connection instructions to users."),
    SettingDef("vpn.public_host", "", "string", "remote",
               "Public DNS name or IP friends can reach. Forward only the VPN port from your router (no web-port forwarding)."),
    SettingDef("vpn.port", 1194, "int", "remote", "OpenVPN server port to forward from the router to this host."),
    SettingDef("vpn.protocol", "udp", "string", "remote", "OpenVPN transport: udp (recommended) or tcp."),
    SettingDef("vpn.subnet", "10.8.0.0/24", "string", "remote",
               "Private range for VPN clients; must not overlap the lab networks."),
    SettingDef("vpn.client_days", 365, "int", "remote", "Validity of newly issued VPN client certificates (days)."),
    # --- AI study assistant (backend/app/ai) ---
    SettingDef("ai.enabled", False, "bool", "ai", "Turn the AI study assistant on."),
    SettingDef("ai.base_url", "", "string", "ai",
               "OpenAI-compatible API base, e.g. http://127.0.0.1:11434/v1 (Ollama). The key is stored separately."),
    SettingDef("ai.model", "", "string", "ai", "Model name the provider expects, e.g. llama3.1:8b."),
    SettingDef("ai.allow_external_provider", False, "bool", "ai",
               "Allow a provider outside this host/LAN (prompts then leave your network)."),
    SettingDef("ai.timeout_seconds", 120, "int", "ai",
               "Longest wait for the model's next output before giving up (it can be slow to start)."),
    SettingDef("ai.max_tokens", 1024, "int", "ai", "Longest answer in tokens."),
    SettingDef("ai.temperature", 0.3, "float", "ai", "Sampling temperature (0-2)."),
    SettingDef("ai.rate_per_minute", 20, "int", "ai", "Chat requests allowed per user (or token) per minute."),
    SettingDef("ai.system_prompt", "", "string", "ai", "Extra instructions added to the assistant's built-in prompt."),
    # --- backups ---
    SettingDef("backup.location", "", "string", "backup",
               "Backup output directory (blank = data_dir/backups)."),
    SettingDef("backup.include_disposable_disks", False, "bool", "backup",
               "Include disposable VM overlays in backups (usually unnecessary)."),
    # --- UX ---
    SettingDef("ui.theme", "dark", "string", "ui",
               "Default theme: dark | light."),
    SettingDef("ui.gamification", True, "bool", "ui",
               "Show XP, streaks and achievements. Admins may disable."),
    SettingDef("ui.show_streak", True, "bool", "ui",
               "Show the learning streak counter on the dashboard."),
    SettingDef("ui.notifications", True, "bool", "ui",
               "Show in-app notifications for jobs and achievements."),
    SettingDef("ui.hints_enabled", True, "bool", "ui",
               "Allow learners to reveal optional hints."),
    SettingDef("ui.walkthroughs_enabled", True, "bool", "ui",
               "Allow learners to reveal optional step-by-step walkthroughs."),
    SettingDef("terminal.scrollback", 2000, "int", "terminal",
               "xterm.js scrollback buffer size."),
    SettingDef("terminal.font_size", 14, "int", "terminal",
               "Default terminal font size."),
    # --- progression ---
    SettingDef("progression.enforce_prerequisites", True, "bool", "progression",
               "Warn/soft-lock courses whose prerequisites are unmet (admin override)."),
    SettingDef("progression.allow_bypass", True, "bool", "progression",
               "Let learners explicitly bypass recommendations with a warning."),
    SettingDef("progression.mastery_threshold", 3, "int", "progression",
               "Competency level (0-4) counted as 'mastered'."),
]

_DEFAULT_MAP = {d.key: d for d in DEFAULTS}


def ensure_defaults(session: Session) -> int:
    """Insert any missing settings. Returns number inserted. Idempotent."""
    existing = set(session.execute(select(Setting.key)).scalars())
    inserted = 0
    for d in DEFAULTS:
        if d.key not in existing:
            session.add(Setting(key=d.key, value=d.default, value_type=d.value_type,
                                category=d.category, description=d.description))
            inserted += 1
    session.flush()
    return inserted


def get_setting(session: Session, key: str, default: Any = None) -> Any:
    row = session.get(Setting, key)
    if row is not None:
        return row.value
    if key in _DEFAULT_MAP:
        return _DEFAULT_MAP[key].default
    return default


def set_setting(session: Session, key: str, value: Any, updated_by: int | None = None) -> Setting:
    if key not in _DEFAULT_MAP:
        raise KeyError(f"Unknown setting '{key}'")
    d = _DEFAULT_MAP[key]
    value = _coerce(value, d.value_type)
    row = session.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value, value_type=d.value_type,
                      category=d.category, description=d.description, updated_by=updated_by)
        session.add(row)
    else:
        row.value = value
        row.updated_by = updated_by
    session.flush()
    return row


def all_settings(session: Session) -> list[Setting]:
    ensure_defaults(session)
    return list(session.execute(select(Setting).order_by(Setting.category, Setting.key)).scalars())


def _coerce(value: Any, value_type: str) -> Any:
    try:
        if value_type == "int":
            return int(value)
        if value_type == "float":
            return float(value)
        if value_type == "bool":
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)
        if value_type == "list":
            if isinstance(value, str):
                return [v.strip() for v in value.split(",") if v.strip()]
            return list(value)
        return value if value is None else str(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Cannot coerce {value!r} to {value_type}") from exc
