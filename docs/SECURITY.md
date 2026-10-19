# Security

Pwnforge manages a hypervisor and runs deliberately vulnerable training targets,
so its own security is a first-class concern.

## Application security

- **Passwords**: Argon2id (argon2-cffi). Never stored or logged in plaintext.
- **Sessions**: an opaque server-side session id, signed with `itsdangerous`
  and set as an `HttpOnly`, `SameSite=Lax` cookie (`Secure` over HTTPS).
  Sessions are revocable server-side and are invalidated on password change.
- **Assessment answers & flags**: only salted SHA-256 hashes are stored; the
  correct value never ships to the browser. Grading is **server-side only** —
  the frontend cannot grant progress or points.
- **Authorisation**: role-based (administrator/instructor/learner/viewer). Every
  VM, lab and terminal is checked for per-user ownership on every request.
  Being on the LAN grants nothing by itself.
- **Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, and a Content-Security-Policy restricting
  scripts/connections to self (plus `ws:`/`wss:`).
- **CORS**: localhost always; additional LAN origins only when configured.
- **Rate limiting**: auth endpoints are rate-limited per IP.
- **Input/validation**: Pydantic schemas validate request bodies; SQLAlchemy
  uses parameterised queries; path/command handling avoids injection (no shell
  interpolation of user input).
- **Audit**: security-relevant actions are logged with secrets redacted.

## Virtualisation security

- Pwnforge **does not run as root**. On Debian it runs as a dedicated user in the
  `libvirt`/`kvm` groups; the systemd unit adds `NoNewPrivileges`,
  `ProtectSystem`, `ProtectHome`, `PrivateTmp`.
- The libvirt management socket is **never** exposed to the frontend. Only the
  backend, through the driver, talks to it.
- Frontend input never becomes a privileged host command. Orchestration is
  expressed through the typed driver interface, not arbitrary shell.
- **Networking defaults to isolated.** Vulnerable targets are not bridged to the
  physical LAN. External/NAT connectivity requires both the global
  `network.allow_external` setting and an explicit per-lab request, with a
  warning. A "no external connectivity" mode is the default.
- Guests are treated as potentially hostile. Host directories are not mounted
  into vulnerable guests.

## Guest terminals

The browser terminal is an **authorised bridge to the intended guest only**, and
never a host shell. Ownership is re-checked on every WebSocket connection. A
production host without a configured hypervisor cannot start labs. The tiny
simulation terminal exists only for automated tests. A separate host-admin
terminal is intentionally **not** implemented.

## Honesty guarantees

- A VM is reported `running` only after the hypervisor confirms it.
- Production reports an unavailable VM backend and blocks new VM starts when a
  real hypervisor is not configured. QEMU TCG is labelled as software emulation
  but still boots real guest operating systems.

## Reporting

For a real deployment, run `/code-review` or your own review over changes, keep
dependencies patched (`pip install -U -r backend/requirements.txt` against a
pinned set), and restrict network exposure to localhost/VPN.

## Unverified on this build

The project was developed and tested on **macOS (Apple Silicon)**, which has no
KVM/libvirt, so the **libvirt driver's real VM boot, snapshots and VNC console
are implemented but unverified here**. They are the production path on Debian
and are exercised there. Everything else (API, DB, auth, catalogue, learning
system, capacity, networking allocation, simulation lifecycle, CLI, frontend
build, 51 tests) is verified — see [../DELIVERY.md](../DELIVERY.md).
