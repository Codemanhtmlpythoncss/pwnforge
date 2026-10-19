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
| Virtualisation | Real libvirt/QEMU guests; KVM acceleration when available, QEMU TCG otherwise |
| Terminals | Browser xterm.js terminal over authorised WebSocket |
| Tests | **51 automated tests, all passing** |

See [DELIVERY.md](DELIVERY.md) for the full acceptance report, including what is
verified vs. unverified on which host.

---

## Quick start (learning platform, any host)

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

## Connect to lab machines from macOS or Linux

When the PwnForge host has enabled direct lab access and the Tailscale subnet
route has been approved, install the small client command on your Mac:

```sh
curl -fsSL https://raw.githubusercontent.com/Codemanhtmlpythoncss/nodeyard/tailnet-lab-access/share/nodeyard/dashboard/web/pwnforge-install-macos.sh | sh
pwnforge install 10.200.0.0/16 <server-lan-ip>
```

For a Linux client with systemd and iproute2:

```sh
curl -fsSL https://raw.githubusercontent.com/Codemanhtmlpythoncss/nodeyard/tailnet-lab-access/share/nodeyard/dashboard/web/pwnforge-install-linux.sh | sh
pwnforge install 10.200.0.0/16 <server-lan-ip>
```

Use the lab network and server LAN address shown by the Nodeyard dashboard.
After installation, `pwnforge status` shows which route is active,
`pwnforge test <lab-IP> 22` checks a running target, and `pwnforge remove`
removes the client helper. The helper adds a persistent LAN fallback and
leaves approved Tailscale routes in control. On Linux, enable route acceptance
if needed with `sudo tailscale set --accept-routes=true`.

The installers install the client command at `/usr/local/bin/pwnforge`. They
stop rather than overwrite an unrelated command already using that name. Do
not install the client helper on the PwnForge server itself; configure its
routes from the Nodeyard dashboard.

The [Nodeyard GitHub README](https://github.com/Codemanhtmlpythoncss/nodeyard/tree/tailnet-lab-access#pwnforge-lab-access-from-a-mac-or-linux-client)
has the same instructions and dashboard download links.

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

- **libvirt** — production path for Debian/Linux hosts (copy-on-write QCOW2
  overlays on golden images, isolated libvirt networks, snapshots, VNC). It
  uses KVM acceleration when available and QEMU software emulation otherwise;
- **qemu** — direct QEMU process management where libvirt is absent;

Production never substitutes a pretend guest for a real VM. If no supported
Linux QEMU/libvirt backend is configured, PwnForge reports that VM hosting is
unavailable and blocks lab launches. The simulation driver is used only by the
automated test suite.

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
