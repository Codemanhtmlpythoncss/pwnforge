# Pwnforge

A fully self-hosted cybersecurity training and virtual-lab platform. Pwnforge
combines a professional, locally hosted website, a real backend API, a
persistent database, a difficulty-based learning system, and a real
virtual-machine orchestration subsystem — so a learner can progress from
beginner fundamentals through to expert, hands-on labs on their own machine,
with no mandatory cloud service.

> **Design principle:** store operating systems once, reuse compatible golden
> images, create disposable environments on demand, and track each learner's
> progress independently of VM state.

---

## What's in the box (verified)

| Area | Status |
|------|--------|
| Courses | **89** substantial courses (≥ 50 required) — `pwnforge courses validate` → 0 issues |
| VM profiles | **1,440** distinct, meaningful profiles (≥ 1,000 required) — `pwnforge profiles validate` → 0 invalid |
| Learning paths | 10 beginner-to-expert paths |
| Multi-machine labs | 11 labs on isolated virtual networks |
| Competencies | 96 across 13 domains, with server-side tracking |
| Difficulty levels | Orientation → Beginner → Easy → Intermediate → Hard → Advanced → Expert → Mastery |
| Website | React + TypeScript + Vite SPA, dark/light theme, served by the backend |
| API | FastAPI, ~60 documented endpoints + OpenAPI at `/api/docs` |
| Database | SQLite + SQLAlchemy + Alembic migrations (PostgreSQL-ready) |
| Virtualisation | libvirt/KVM (Debian) · QEMU · honest **simulation** driver |
| Terminals | Browser xterm.js terminal over authorised WebSocket |
| Tests | **51 automated tests, all passing** |

See [DELIVERY.md](DELIVERY.md) for the full acceptance report, including what is
verified vs. unverified on which host.

---

## Quick start (development, any host)

```bash
cd pwnforge
python3 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e .                      # provides the `pwnforge` command

# initialise DB + import catalogue + create an admin
pwnforge init

# build the website
cd frontend && npm install && npm run build && cd ..

# run it
pwnforge serve
# open http://localhost:8080
```

On first launch the site asks you to create the administrator account and binds
to **localhost only**. LAN access is an explicit setting (Admin → Settings →
`server.lan_access`).

## Production install (Debian + KVM)

```bash
sudo apt install qemu-system-x86 qemu-utils libvirt-daemon-system python3-libvirt nodejs npm
bash scripts/install/install.sh          # safe to re-run; never overwrites data
```

Then optionally install the systemd service in `deploy/systemd/pwnforge.service`.
See [docs/INSTALLATION.md](docs/INSTALLATION.md) for the full guide.

> **No OS images are ever downloaded automatically.** Base images are fetched
> only when you explicitly run `pwnforge images fetch <key>` on the host.

---

## The learning model

Every course, lesson, lab and VM profile carries a difficulty and (where
relevant) prerequisites. The platform:

- recommends the next course from your **demonstrated competencies**, not just
  what you've opened;
- **soft-locks** advanced material when prerequisites are unmet, but lets you
  proceed with a warning (admins can override);
- tracks competencies server-side — the browser cannot grant itself progress;
- validates assessments **server-side** (correct answers never ship to the
  client; only salted hashes are stored);
- offers **optional hints, steps and walkthroughs** on lessons and exercises —
  revealing them is never penalised, only recorded to refine recommendations.

See [docs/LEARNING_PATHS.md](docs/LEARNING_PATHS.md).

## Virtualisation & storage

A pluggable driver runs the identical orchestration code against:

- **libvirt** — production path for Debian/KVM hosts (copy-on-write QCOW2
  overlays on golden images, isolated libvirt networks, snapshots, VNC);
- **qemu** — direct QEMU process management where libvirt is absent;
- **simulation** — a deterministic, clearly-labelled stand-in for hosts without
  a hypervisor (e.g. macOS, CI). It never claims to be a real hypervisor; its
  VMs are flagged `simulated` everywhere in the UI and API.

Storage is layered — ISOs → immutable golden images → reusable components →
copy-on-write overlays — with image-dependency tracking and safe,
dry-run-first garbage collection. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Repository layout

```
pwnforge/
├── backend/app/          FastAPI app, services, drivers, catalogue
│   ├── api/              HTTP + WebSocket routes
│   ├── auth/ security/   auth, crypto, audit
│   ├── courses/ competencies/ learning_paths/   learning system
│   ├── profiles/ labs/ vms/ images/ networks/ storage/ jobs/   infra
│   ├── catalog/content/  authored courses, profiles, paths, images
│   └── database/         models, engine, migrations entrypoint
├── backend/migrations/   Alembic migrations
├── backend/tests/        pytest suite (51 tests)
├── frontend/             React + TS + Vite SPA
├── catalog/              materialised YAML/JSON catalogue (see build_catalog)
├── scripts/              install / diagnostics
├── deploy/systemd/       service unit
└── docs/                 full documentation
```

## CLI

```
pwnforge status          pwnforge doctor            pwnforge serve
pwnforge courses list    pwnforge courses validate  pwnforge paths list
pwnforge profiles stats  pwnforge profiles search   pwnforge profiles validate
pwnforge images list     pwnforge images fetch KEY  pwnforge images prune --dry-run
pwnforge storage         pwnforge backup
```

## Licence & intent

Pwnforge is for **authorised** security education: your own machine, isolated
labs, learning. All course content is original and defensive/educational in
framing. It must not be used to attack systems you do not own or have explicit
permission to test.
