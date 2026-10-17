# Troubleshooting

Start with `hacklab doctor` — it checks host virtualisation, catalogue counts
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

**Driver is `simulation` on a Linux host that has KVM** — check `/dev/kvm`
exists and you're in the `kvm`/`libvirt` groups (`id`), and that
`python3-libvirt`/`virsh` are installed. `hacklab status` shows the detected
host and selected driver.

**VM start fails: "Base image … is absent"** — fetch it on the host:
`hacklab images fetch debian-13-base` (or build role images from it). Nothing is
downloaded automatically.

**VM start fails: "RAM/vCPU budget exceeded"** — raise the limits in Admin →
Settings (`vm.max_total_memory_mb`, `vm.max_total_vcpu`, `vm.max_concurrent`),
within what the host can actually provide.

**VM start fails: "Insufficient host RAM"** — the host genuinely lacks free
memory beyond `vm.reserve_host_memory_mb`. Stop other VMs or add RAM. HackLab
refuses to overcommit physical memory.

**A VM shows a wrong state** — Admin → Overview → *Reconcile*, or
`POST /api/admin/reconcile`. This re-reads actual hypervisor state.

**Lab partially started then stopped** — a stage failed (often capacity). Only
that lab's resources are torn down. Check the job's steps
(`GET /api/jobs/{id}`) and the lab instance's `last_error`.

## Terminal

**Simulated terminal / "no host shell is exposed"** — expected when the active
driver is `simulation` (e.g. on macOS). Deploy on a KVM host for a live guest
console.

**"Not authorised for this VM"** — you don't own that VM (and aren't an admin).

## Storage

**Low-space warning** — free space is below `storage.low_space_warn_gb`. Run
Admin → Storage → *Cleanup (dry run)* to find orphan overlays, then clean up.

## Database / migrations

**`alembic upgrade head` errors** — ensure `HACKLAB_DATA_DIR` points at the
right place and the venv is active. For a brand-new DB you can also bootstrap
with `python -c "from backend.app.database.init_db import initialise; initialise()"`.

## Logs

Application logs are under `<data>/logs/`. Run the server in the foreground
(`hacklab serve`) to watch request logs during debugging.
