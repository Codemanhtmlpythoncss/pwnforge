# Troubleshooting

Start with `pwnforge doctor` — it checks host virtualisation, catalogue counts
and the image dependency graph.

## Website

**Backend returns a JSON placeholder at `/`** — the frontend isn't built. Run
`cd frontend && npm install && npm run build`. The backend serves
`frontend/dist` automatically once it exists.

**"Authentication required" / redirected to login** — your session expired
(`auth.session_ttl_hours`) or cookies are blocked. Sign in again.

**Can't reach from another device** — LAN access is off by default. Admin →
Settings → `server.lan_access = true`, then browse to `http://<host-ip>:8080`.

## Virtualisation

**VM hosting is unavailable** — install QEMU, qemu-img, libvirt and its Python
binding, then run the dashboard's **Set up real machines** action (or follow
the installation steps). If `/dev/kvm` is absent, QEMU TCG still boots real
VMs but will be slower. PwnForge blocks lab launches until a real backend is
ready; it does not silently simulate a guest.

**VM start fails: "Base image … is absent"** — fetch it on the host:
`pwnforge images fetch debian-13-base` (or build role images from it). Nothing is
downloaded automatically.

**VM start fails: "RAM/vCPU budget exceeded"** — raise the limits in Admin →
Settings (`vm.max_total_memory_mb`, `vm.max_total_vcpu`, `vm.max_concurrent`),
within what the host can actually provide.

**VM start fails: "Insufficient host RAM"** — the host genuinely lacks free
memory beyond `vm.reserve_host_memory_mb`. Stop other VMs or add RAM. Pwnforge
refuses to overcommit physical memory.

**A VM shows a wrong state** — Admin → Overview → *Reconcile*, or
`POST /api/admin/reconcile`. This re-reads actual hypervisor state.

**Lab partially started then stopped** — a stage failed (often capacity). Only
that lab's resources are torn down. Check the job's steps
(`GET /api/jobs/{id}`) and the lab instance's `last_error`.

## Terminal

**No live guest console** — check that the VM is running with a real driver and
that it has a serial console configured. The simulation backend is reserved for
automated tests.

**"Not authorised for this VM"** — you don't own that VM (and aren't an admin).

## Storage

**Low-space warning** — free space is below `storage.low_space_warn_gb`. Run
Admin → Storage → *Cleanup (dry run)* to find orphan overlays, then clean up.

## Database / migrations

**`alembic upgrade head` errors** — ensure `PWNFORGE_DATA_DIR` points at the
right place and the venv is active. For a brand-new DB you can also bootstrap
with `python -c "from backend.app.database.init_db import initialise; initialise()"`.

## Logs

Application logs are under `<data>/logs/`. Run the server in the foreground
(`pwnforge serve`) to watch request logs during debugging.
