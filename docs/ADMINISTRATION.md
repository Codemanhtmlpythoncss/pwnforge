# Administration

Administrators get two extra sections: **Administration** and **Settings**.

## Administration

- **Overview** — the active virtualisation driver and host capabilities
  (honestly reporting whether real virtualisation is available), catalogue
  counts, image-chain health, and a **Reconcile** button that re-syncs the
  database with the hypervisor's actual VM state.
- **Images** — the golden-image registry. *Fetch* downloads/builds an image
  **on the host, only when you click it** (never automatically). *Verify*
  checks the checksum. Virtual vs actual sizes are shown.
- **Storage** — physical free space, image/overlay consumption, and a
  dry-run cleanup that lists orphaned overlays before anything is removed.
- **Users** — list and create users with roles (administrator, instructor,
  learner, viewer). New users must change their password on first login.
- **Audit** — a searchable log of security-relevant actions. Secrets are never
  recorded (values are redacted).

## Settings

Every setting has a real backend consumer. Notable groups:

- **server** — `server.port`, `server.lan_access` (bind 0.0.0.0 for authorised
  LAN devices), `server.allowed_origins`.
- **auth** — session TTL, registration open/closed, minimum password length.
- **resources** — `vm.max_total_memory_mb` (the **RAM budget** — fully
  customisable), `vm.max_total_vcpu`, `vm.max_concurrent`,
  `vm.ram_overcommit_ratio`, `vm.reserve_host_memory_mb`, default VM
  resources, and an optional `vm.per_user_memory_mb` budget (0 = disabled).
- **lifecycle** — auto-shutdown and idle timeouts.
- **storage** — image cache cap, snapshot retention, cleanup policy, low-space
  warning threshold.
- **network** — default mode (isolated), `network.allow_external` (off by
  default), the supernet subnets are carved from.
- **backup** — output location, whether to include disposable disks.
- **ui** — theme, gamification on/off, hints/walkthroughs enabled, notifications.
- **progression** — enforce prerequisites, allow bypass, mastery threshold.

### Changing the RAM allowance

Admin → Settings → `vm.max_total_memory_mb`. This caps total RAM committed
across running VMs. On a real host, `vm.reserve_host_memory_mb` is kept free for
the host and HackLab refuses to start a VM that would exceed physical RAM (it
never silently overcommits). Simulated VMs consume no real RAM, so only the
configured budget applies to them.

## Access modes

1. **Localhost** (default) — the safest mode.
2. **LAN** — set `server.lan_access = true` to bind 0.0.0.0. Add LAN URLs to
   `server.allowed_origins` if you use the dev frontend. Only authenticated
   users get in; being on the network does not make you an admin.
3. **Secure remote** — put HackLab behind a VPN or an authenticated reverse
   proxy. Do **not** expose the management site directly to the internet.

## Recovery

If you lose web access, use the CLI on the host:

```bash
hacklab doctor                      # diagnose
# create a replacement admin (only works if none exists):
hacklab init --admin-user newadmin
```

To reset a locked-out admin's password, open a Python shell with the venv and
use `backend.app.auth.service.change_password`, or create a new admin after
removing the old row — document your own org procedure.

## Course & profile authoring

See [COURSE_AUTHORING.md](COURSE_AUTHORING.md) and
[PROFILE_AUTHORING.md](PROFILE_AUTHORING.md). New content is added to the
versioned catalogue and imported idempotently — updating content never erases
learner progress or achievements.
