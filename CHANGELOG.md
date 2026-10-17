# Changelog

## 1.0.0 — 2026-10-17

Initial release of Pwnforge.

### Platform
- FastAPI backend with ~60 documented endpoints + OpenAPI at `/api/docs`.
- SQLAlchemy models (29 tables) with Alembic migrations; SQLite (WAL) default,
  PostgreSQL-ready.
- React + TypeScript + Vite SPA (dark/light), served by the backend; xterm.js
  browser terminal over authorised WebSockets.
- Argon2 passwords, signed+revocable sessions, RBAC, audit logging, CSP and
  security headers, auth rate limiting.

### Learning
- 60 original cybersecurity courses with lessons, exercises, assessments and
  **optional hints/steps/walkthroughs**.
- 8 beginner-to-expert learning paths; 77 competencies across 12 domains with
  server-side tracking and recommendations.
- Server-side assessment/flag validation; difficulty + prerequisite system with
  soft-locking and admin override; achievements and XP (disableable).

### Virtualisation
- Driver abstraction with libvirt/KVM (production), QEMU, and an honest
  simulation driver.
- Staged VM lifecycle (create/start/stop/reboot/reset/snapshot/delete) that only
  reports "running" after the hypervisor confirms it; state reconciliation.
- 1,040 distinct VM profiles; 10 multi-machine labs on isolated networks.
- Copy-on-write QCOW2 overlays on golden images; image dependency tracking;
  physical-vs-virtual storage reporting; dry-run garbage collection.
- Capacity planner with customisable RAM/CPU/concurrency budgets and host-RAM
  protection.

### Operations
- `pwnforge` CLI (status, doctor, serve, courses, paths, profiles, images,
  storage, backup, init) sharing the same services as the website.
- Debian installer, systemd unit, backup/verify, diagnostics.
- 51 automated tests, all passing.

### Notes
- Developed and verified on macOS (Apple Silicon) using the simulation driver.
  The libvirt driver's real VM boot/snapshots/VNC are implemented but unverified
  on this host (production path is Debian/KVM). See DELIVERY.md.
- No OS images are ever downloaded automatically.
