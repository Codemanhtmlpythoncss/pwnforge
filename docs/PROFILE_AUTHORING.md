# Profile Authoring

A **profile** describes a training environment (OS base, resources, services,
objectives, difficulty) — not necessarily a complete OS image. Profiles are
produced by a deterministic pipeline in
`backend/app/catalog/content/profiles.py` from three meaningful dimensions:

- **THEME** — the learning scenario (what it teaches/exercises) and its
  competency, course association and difficulty range.
- **STACK** — the concrete software stack and golden base image + OS family.
- **LEVEL** — difficulty, which scales resources, objectives and independence.

Each `(theme × stack × level)` cell is a distinct, meaningful environment; a set
of named component variants (`_COMPONENTS`) adds further realistic targets. The
generator asserts a minimum catalogue size (`MIN_PROFILES = 1000`) and unique
ids, so the count is real — not padded duplicates.

## Add a theme

```python
Theme("my-theme", "My Scenario Lab", "web-security", "sql-injection",
      course="sql-injection-labs",
      objective="Recognise and remediate the issue.",
      levels=["intermediate", "hard"], stacks=WEB_STACKS, tags=["web"]),
```

## Add a stack (and base image)

```python
Stack("my-stack", "Display name", "debian", "debian-13-web",
      packages=["nginx"], services=["nginx"]),
```

Register the base image in `content/images.py` (Debian is the primary
foundation; role images are copy-on-write children via `parent`).

## A profile record

```yaml
id: sqli-nginx-php-i
name: "SQL Injection Lab — nginx + PHP-FPM (standard)"
category: web-security
difficulty: intermediate
os_family: debian
base_image_key: debian-13-web
vcpu: 2
memory_mb: 2048
disk_gb: 12
network_mode: isolated
packages: [nginx, php-fpm]
services: [nginx, php-fpm]
objectives: [...]
prerequisites: [sql-injection-labs]
lifecycle: { reset_supported: true, snapshots_supported: true, disposable: true }
```

## Readiness

Profiles are never shown as "ready" unless launchable:

| Readiness | Meaning |
|-----------|---------|
| `ready` | Base image present (real driver) or simulation active |
| `requires_base_image` | Image not downloaded/built |
| `requires_install_media` | Needs an ISO (e.g. Windows) |
| `requires_manual_config` | No base image key |
| `unsupported_on_host` | Arch not supported by the host |
| `invalid` / `failed_provisioning` | Problems |

Readiness is recomputed from host capabilities + image state
(`profiles.recompute_readiness`).

## Validate

```bash
hacklab profiles validate     # schema + required fields, 0 invalid expected
hacklab profiles stats        # counts by category/difficulty/os/readiness
hacklab profiles search TERM
```
