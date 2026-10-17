# Architecture

## Overview

Pwnforge is a single deployable application with three layers:

1. **Frontend** — a React/TypeScript SPA (Vite build) served as static files by
   the backend. It talks only to the JSON API and WebSocket endpoints.
2. **Backend** — FastAPI + SQLAlchemy. All business logic lives in framework-
   agnostic *service* modules; the HTTP routes and the CLI are thin shells over
   the same services, so they can never drift apart.
3. **Virtualisation** — a driver abstraction that the orchestration services
   call. The same code runs against libvirt/KVM, QEMU, or a simulation driver.

```
Browser ──HTTP/WS──> FastAPI routes ──> services ──> SQLAlchemy ──> SQLite/Postgres
                                   └──> VM driver  ──> libvirt / qemu / simulation
Background jobs (ThreadPool) ──> services (staged VM/lab lifecycle)
```

## Request & job flow

- Short operations run inline in the request.
- Long operations (VM start, lab start, image fetch) are **background jobs**
  recorded in the `jobs` table. The route returns a `job_id`; the client polls
  `GET /api/jobs/{id}` or subscribes to `ws /api/ws/jobs/{id}` for live stage
  and percentage progress. Each job runs on its own DB session, commits per
  stage (so progress is visible and SQLite's single writer is never contended
  by a second connection in the same thread), and holds a per-target lock so
  two operations can never corrupt one VM.

## Service modules (`backend/app/`)

| Module | Responsibility |
|--------|----------------|
| `core/config.py` | Bootstrap config (paths, DB URL, secret, bind) |
| `core/settings_service.py` | Runtime, DB-backed settings registry (every key has a consumer) |
| `core/host_monitor.py` | Real host CPU/RAM/disk via psutil |
| `auth/` + `security/` | Argon2 passwords, signed+revocable sessions, audit log, answer/flag hashing |
| `courses/` | Course delivery, progress, **server-side** assessment validation, hints/walkthroughs, recommendations, achievements |
| `competencies/` | 0–4 competency map, evidence-based level-ups |
| `learning_paths/` | Path progression, soft-locking, next step |
| `profiles/` | Catalogue search/filter/stats; readiness computation |
| `vms/` | Driver abstraction + staged lifecycle + capacity planner + reconciliation |
| `labs/` | Multi-machine orchestration with scoped teardown |
| `images/` | Golden-image registry, checksum verify, **explicit-only** fetch, dependency graph |
| `networks/` | Isolated per-lab subnet allocation |
| `storage/` | Physical-vs-virtual reporting, dry-run GC of orphan overlays |
| `jobs/` | Background runner + job handlers |
| `catalog/` | Authored content + importer (idempotent, preserves learner state) |

## Virtualisation driver contract

`backend/app/vms/driver.py` defines `VMDriver` with `capabilities()`,
`create_overlay`, `create_network`, `define/start/stop/reboot/delete`,
`status`, `get_ip`, `console`, and snapshot methods. Drivers raise
`DriverUnsupported` for capabilities they cannot honestly perform; the
orchestration layer refuses the operation rather than faking it.

`HostCapabilities.real_virtualization` is the honesty flag. The simulation
driver returns `False`, and every instance it creates is marked
`driver="simulation"` and surfaced as `simulated: true` in the API and UI.

### Staged VM startup

`vms/service.start_instance` runs 14 stages (validate profile → check host →
check capacity → check storage → resolve image → verify image → create overlay
→ define → configure network → start → wait for running → discover IP → check
services → mark ready). It only sets status `running` **after the driver
confirms** the domain is running (`_wait_running`). On failure it records the
error and cleans up the overlay it created.

### Storage model

```
Layer 1  Installation ISOs (immutable, checksum-verified)
Layer 2  Immutable golden images (Debian base + role children via backing files)
Layer 3  Reusable provisioning components (packages/services per profile)
Layer 4  Copy-on-write QCOW2 overlays (one per disposable VM)
Layer 5  Image cache + dependency tracking
Layer 6  Safe, dry-run-first garbage collection
```

A new disposable VM is a thin overlay (`qemu-img create -b <golden>`); N VMs on
one golden image cost ~one base + N small deltas. Parent images are never
deleted while a dependent references them (`images.can_delete`).

## Database

29 tables (see `backend/app/database/models.py`). Content (courses, lessons,
profiles, labs, paths) is imported from the authored catalogue; learner state
(progress, competencies, achievements, submissions) and infrastructure state
(VM instances, networks, snapshots, jobs, reservations) live only in the DB.
SQLite runs in WAL mode with enforced foreign keys. Alembic manages schema;
`backend/app/database/init_db.py` provides a create-all bootstrap for tests.

Swapping to PostgreSQL is a `PWNFORGE_DATABASE_URL` change plus `alembic upgrade
head`.
