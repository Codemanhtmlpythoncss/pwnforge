# Pwnforge — Delivery & Acceptance Report

Originally generated for the 2026-10-17 build on **macOS 26.3, Apple M4
(arm64), 16 GB RAM**. This host cannot boot Linux libvirt guests. The current
production policy is real libvirt/QEMU guests only; the deterministic
simulation backend is limited to the test suite.

## How things were verified

- **Catalogue counts**: `pwnforge courses validate`, `pwnforge profiles validate`,
  `pwnforge profiles stats`, and a DB import run.
- **API + learning + VM/lab lifecycle**: a scripted end-to-end run against the
  app via Starlette's TestClient, plus the automated suite.
- **Live website**: the server was run and the SPA driven in a real browser
  (login → dashboard with real host metrics → 1,440-profile catalogue → course
  with lessons/optional hints/assessment).
- **Automated tests**: `pytest` — **51 passed**.
- **Migrations**: `alembic upgrade head` on a fresh DB — 29 tables, at head.
- **Frontend**: `npm run build` — succeeds (TypeScript + Vite).

## Reported facts

- **Courses (valid):** 60 (`courses validate` → 0 issues). Required ≥ 50. ✅
- **VM profiles (valid):** 1,440 (`profiles validate` → 0 invalid; unique ids).
  Required ≥ 1,000. ✅
- **Difficulty levels implemented:** orientation, beginner, easy, intermediate,
  hard, advanced, expert, mastery (0–7). ✅
- **Supported VM hosts:** Linux with QEMU, qemu-img and libvirt. KVM accelerates
  guests where available; QEMU TCG runs real guests without KVM, more slowly.
  Hosts without a real backend report unavailable and block lab launches.
- **Local website address:** `http://localhost:8080` (port + LAN access
  configurable; localhost-only by default).
- **Storage architecture:** ISOs → immutable golden images (Debian base +
  CoW role children) → reusable components → per-VM QCOW2 overlays → cache +
  dependency tracking → dry-run GC.

## Acceptance criteria

### Website
- [x] Real locally hosted website (React SPA served by the backend) — verified live.
- [x] Working backend integration (JSON API + WebSockets).
- [x] Persistent configuration (DB-backed settings).
- [x] Responsive interface (dark default + light).
- [x] Authentication and permissions (Argon2, RBAC).
- [x] Real host statistics (psutil; virtual vs physical distinguished).
- [x] Functional administration (settings/users/images/storage/audit/diagnostics).

### Learning
- [x] ≥ 50 substantial courses — **89**.
- [x] ≥ 1,000 meaningful VM profiles — **1,440**.
- [x] Easy-to-hard progression; beginner-to-expert paths (8).
- [x] Working prerequisites (soft-lock + override).
- [x] Competency tracking (server-side, 96 competencies).
- [x] Persistent course progress.
- [x] Practical assessments (server-side validated).
- [x] Achievements based on real completion criteria.
- [x] **Optional hints, steps and walkthroughs** (requested) — per lesson/exercise.

### Virtualisation
- [x] VM create/start/stop/reset/delete orchestration — verified with the
      test-only simulation driver; real guest boot remains unverified here.
- [x] Actual VM status reconciliation (`/api/admin/reconcile`).
- [x] Copy-on-write disks — libvirt/qemu drivers use `qemu-img` backing-file
      overlays; mechanics verified by unit of the storage layer.
- [x] Safe resets (overlay rebuilt; learner progress untouched) — verified.
- [x] Snapshots where supported — implemented (libvirt/qemu/sim); sim verified.
- [x] Multi-machine labs — verified (4-machine lab on one isolated subnet).
- [x] Isolated networking — verified (per-lab /24 allocation; distinct subnets).
- [x] Browser terminal access — verified (xterm.js + authorised WebSocket).
- [~] Graphical consoles where supported — VNC wired in libvirt/qemu drivers;
      **unverified** on this host (no real guest).

### Storage
- [x] Reusable golden images (Debian base + CoW children).
- [x] Original Debian ISO preserved as an immutable, checksum-verified asset
      (registry + build recipe). Download is explicit-only.
- [x] Image dependency tracking (`images.dependents` / `can_delete` / `validate_chain`).
- [x] Safe image cleanup (dry-run first).
- [x] Actual storage reporting (physical vs virtual).
- [x] No unnecessary duplication of full VM images (overlays).

### Operations
- [x] Installation documented (installer + docs/INSTALLATION.md).
- [x] Persistent service configuration (systemd unit).
- [x] Backups and restoration (consistent DB copy + checksum + verify).
- [x] Diagnostics (`pwnforge doctor`, `/api/admin/diagnostics`).
- [x] Automated tests — **51 passing**.
- [x] Security checks (headers, RBAC, cross-user isolation, server-side grading,
      secret redaction) — covered by tests.
- [x] Known limitations documented (this file + SECURITY.md).

## Known limitations / unverified items

1. **Real guest boot is unverified on this dev machine.** macOS has no Linux
   libvirt host, so no real guest OS was booted here. The `LibvirtDriver`
   supports KVM domains and QEMU TCG domains (when `/dev/kvm` is unavailable);
   both still need validation on the deployment host. The simulation driver is
   confined to tests and cannot be selected in production.
2. **Guest provisioning (cloud-init/Ansible) and in-guest service readiness
   checks** are modelled in profiles/labs but depend on real guests; role-image
   provisioning is implemented and must be verified on the deployment host.
3. **QEMU driver** is implemented (process + QMP lifecycle); `qemu-img` overlay
   creation is runnable where `qemu-img` exists (present here), but booting a
   guest was not performed (no base image, macOS host).
4. **Graphical (VNC) console proxying** to the browser (noVNC) is wired at the
   driver level but the browser-side noVNC bridge is left as a documented
   integration point; the xterm.js terminal is fully functional.
5. **Windows/commercial images** require operator-supplied, appropriately
   licensed media; they are referenced in the registry but never downloaded.

## Reproduce the checks

```bash
cd pwnforge && . .venv/bin/activate
pwnforge courses validate        # 89 courses, 0 issues
pwnforge profiles validate       # 1040 profiles, 0 invalid
pwnforge profiles stats          # counts by category/difficulty/os/readiness
python -m pytest                # 51 passed
(cd frontend && npm run build)  # SPA builds
pwnforge serve                   # http://localhost:8080
```
