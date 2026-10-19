# Improvement backlog — PwnForge & Nodeyard

Evidence-based backlog of 300 distinct, actionable improvements across the two
repositories. Scope tags: **[PF]** PwnForge (`~/Developer/pwnforge`), **[NY]**
Nodeyard (`~/Developer/nodeyard`). Status: `[ ]` open, `[x]` already implemented
(this session or earlier), `[~]` partially present.

Each item: `ID. [status][repo] Title — surface · problem · Impact/Confidence (1–5) · Effort (S/M/L)/Risk (low/med/high) · dep/acceptance`.

Ten highest-value candidates are starred (★) and summarised at the end.

---

## 1. First-run experience & onboarding

1. `[ ][PF]` Role-aware first-run welcome — `frontend/src/App.tsx`, `pages/Login.tsx` · new learner/admin/operator split so the first page matches intent · I4/C3 · M/low · after bootstrap.
2. `[ ][PF]` Setup readiness checklist — `api/routes_infra.py host_caps`, new `pages/Setup.tsx` · surface done/pending/blocked prerequisites (DB, images, virt, network) in one view · I4/C4 · M/low.
3. `[~][PF]` Guided host diagnostics → next steps — `backend/app/cli.py doctor`, `core/host_monitor.py` · `doctor` exists in CLI but is not surfaced in UI with actionable fixes · I4/C4 · M/low · acceptance: each failed check links a guide.
4. `[ ][PF]` Skippable, resumable product tour — new `components/Tour.tsx` · first-time users miss key controls (Labs, Running, Guide) · I3/C3 · M/low.
5. `[~][PF]` Setup wizard with safe-default preview — `pages/Settings.tsx` · settings are a flat table; no preview of effect before Save · I3/C3 · L/med.
6. `[ ][PF]` Progressive disclosure of advanced VM/network settings — `pages/Settings.tsx` groups · hide expert knobs behind a toggle · I3/C4 · S/low.
7. `[x][PF]` Plain-language term explanations — `pages/Guide.tsx` · the new Guide explains target/flag/route; extend to snapshot/overlay/competency · I3/C4 · S/low.
8. `[ ][PF]` Recovery-oriented error pages — `App.tsx` route `*` just redirects to `/` · add a 404/error boundary with contextual actions · I3/C4 · S/low.
9. `[ ][PF]` Global search (courses/labs/machines/settings/help) — new `components/Search.tsx` + `api/routes_*` · no cross-surface search exists · I4/C3 · L/med.
10. `[ ][PF]` Command palette (Cmd-K) for navigation/safe actions — new `components/CommandPalette.tsx` · power-user navigation · I3/C3 · M/low.
11. `[ ][PF]` First-run "create admin" strength meter — `pages/Login.tsx` bootstrap · guide to a strong admin password · I3/C4 · S/low · ties to auth.min_password_length.
12. `[ ][NY]` Dashboard first-run tile for PwnForge install state — `web/pwnforge.js` · shows install/not-installed but no guided next step · I3/C3 · S/low.
13. `[ ][PF]` Sample/demo lab highlighted for first session — `pages/Labs.tsx` · beginners don't know which lab to start · I3/C4 · S/low · pick `linux-practice-basic`.
14. `[ ][PF]` "What can this host run?" capability summary on Machines — `pages/Machines.tsx` · readiness filter exists but no human summary · I3/C3 · S/low.
15. `[ ][PF]` Empty-state guidance on every list page — `pages/{Running,Labs,Certificates}.tsx` · some `Empty` msgs are terse · I2/C4 · S/low.
16. `[ ][NY]` Guided Tailscale HTTPS setup check — `pwnforge-host.sh cmd_https` · failure message is good; add a pre-flight status tile · I3/C3 · S/low.
17. `[ ][PF]` Onboarding progress persisted per user — new column/table · resume onboarding across sessions · I2/C3 · S/low.
18. `[ ][PF]` First lab "connection check" wizard — `pages/LabWorkspace.tsx` · confirm the learner can reach the target before they start · I4/C3 · M/low · depends on ConnectCommands.
19. `[ ][PF]` Inline "why is real-VM unavailable?" explainer — `TopBar` capability chip in `App.tsx` · chip says "real VM setup needed" but not why/how · I4/C4 · S/low.
20. `[ ][NY]` One-command installer link from dashboard → GitHub docs — `web/pwnforge.js` · discoverability of client setup · I3/C3 · S/low.

## 2. Dashboard & navigation usability

21. `[x][PF]` Live host-resource rings actually update — `pages/Dashboard.tsx` · were fetched once; now poll `/api/host/stats` (PR #25) · I3/C5 · S/low.
22. `[ ][PF]` Breadcrumbs preserving filters/scroll — `App.tsx`, list pages · back navigation loses context · I3/C4 · M/low.
23. `[ ][PF]` Pin/favourite courses/labs/machines — new `UserPin` table + `api` · fast re-access · I3/C3 · M/low.
24. `[ ][PF]` Saved table views (filters/sort/columns) on Machines — `pages/Machines.tsx` · 1440 profiles; re-filtering each visit · I3/C4 · M/low.
25. `[~][PF]` Responsive layout for tablet/phone — `App.tsx` sidebar fixed 232px · core tasks cramped on small screens · I3/C3 · M/med.
26. `[ ][PF]` Customisable dashboard widget order — `pages/Dashboard.tsx` · let users hide/reorder tiles · I2/C3 · M/low.
27. `[ ][PF]` Keyboard shortcut for sign-out/theme/nav — `App.tsx` Sidebar · discoverable shortcuts · I2/C3 · S/low.
28. `[ ][PF]` Sticky section headers on long Settings page — `pages/Settings.tsx` · long scroll, hard to find a group · I2/C4 · S/low.
29. `[ ][PF]` Collapsible setting groups with search — `pages/Settings.tsx` · ~30+ settings flat · I3/C4 · S/low.
30. `[ ][PF]` "Running" count badge in sidebar — `App.tsx` Sidebar · see active machines without navigating · I3/C3 · S/low.
31. `[ ][PF]` Consistent icon for lab vs course steps — `pages/PathDetail.tsx` · lab steps now have `kind`; render a lab glyph · I2/C4 · S/low · uses new `kind` field.
32. `[ ][PF]` Recent-activity links to the relevant page — `pages/Dashboard.tsx` · activity rows are text-only · I2/C3 · S/low.
33. `[ ][PF]` Loading skeletons instead of full-page spinner — pages use `<Spinner/>` · perceived performance · I2/C3 · M/low.
34. `[ ][NY]` Mobile dashboard parity audit — `docs/mobile-dashboard.md`, `web/*.js` · verify controls reachable on phones · I3/C3 · M/med.
35. `[ ][PF]` Consistent "copy" affordance styling — multiple pages · copy icons differ (⧉ vs CodeBlock button) · I2/C4 · S/low.
36. `[ ][PF]` Surface host driver + accel in a header tooltip detail — `App.tsx TopBar` · chip shows driver only · I2/C4 · S/low.
37. `[ ][PF]` Dashboard "resume where you left off" card — `learning_paths` next_step · one-click continue · I3/C3 · S/low.
38. `[ ][PF]` Keyboard-navigable machine cards — `pages/Labs.tsx`, `LabWorkspace.tsx` · buttons-in-buttons pattern harms a11y/keys · I3/C3 · M/med.
39. `[ ][PF]` Theme respects system + explicit override already; add high-contrast — `App.tsx toggleTheme`, `index.css` · only light/dark · I3/C3 · M/low.
40. `[ ][PF]` Persist active machine selection in LabWorkspace — `pages/LabWorkspace.tsx` · reselects machines[0] on reload · I2/C4 · S/low.

## 3. Accessibility

41. `[ ][PF]` Add aria-labels across icon-only buttons — only ~12 aria/role attrs in all pages · screen readers miss actions · I4/C5 · M/low.
42. `[ ][PF]` Live-region announcements for job/quiz/flag results — `pages/{LabWorkspace,CourseDetail}.tsx` · status changes silent to SR · I4/C4 · M/low.
43. `[~][PF]` Visible focus ring for keyboard only — `index.css` has `:focus:not(:focus-visible)` · audit all interactive els · I3/C4 · S/low.
44. `[ ][PF]` Skip-to-content link — `App.tsx` · keyboard users tab through sidebar each page · I3/C5 · S/low.
45. `[ ][PF]` Reduced-motion support for toasts/animations — `index.css achToastIn`, `fade-in` · respect `prefers-reduced-motion` · I3/C5 · S/low.
46. `[ ][PF]` Terminal accessibility mode (font size/contrast) — `pages/LabWorkspace.tsx Xterm` · xterm defaults small · I3/C3 · M/low.
47. `[ ][PF]` Form fields associated with labels — `pages/Login.tsx`, `Settings.tsx` · placeholders used as labels · I3/C4 · S/low.
48. `[ ][PF]` Color is not the only status signal — chips rely on color — add text/icon · I3/C4 · S/low.
49. `[ ][PF]` Keyboard-operable hint reveal & copy controls — `LabWorkspace.tsx` · role="button" spans need key handlers · I3/C4 · S/low.
50. `[ ][PF]` Contrast audit of muted text on panels — `index.css` tokens · verify WCAG AA · I3/C4 · S/low.
51. `[ ][PF]` Certificate page print contrast & alt text — `pages/Certificates.tsx` · logo/seal needs alt · I2/C4 · S/low.
52. `[ ][PF]` Announce WS connect/disconnect in terminal — `Xterm` status is visual only · I3/C4 · S/low.
53. `[ ][PF]` Larger hit targets on mobile for nav/controls — `App.tsx` · small tap targets · I3/C3 · S/low.
54. `[ ][PF]` Respect `prefers-contrast` media query — `index.css` · I2/C3 · S/low.
55. `[ ][PF]` Accessible modal/confirm dialogs (focus trap) — AccountReset confirm, future dialogs · I3/C4 · M/med.
56. `[ ][PF]` Alt text / aria on rank & progress rings — `ui.tsx Ring/RankBadge` · SVG without labels · I3/C4 · S/low.
57. `[ ][PF]` Table semantics for Machines/Running lists — div-based rows · use roles or table · I3/C3 · M/med.
58. `[ ][NY]` Dashboard a11y pass (labels, focus, contrast) — `web/*.js`, `web/*.html` · login.html has aria-label on Show; extend · I3/C3 · M/med.
59. `[ ][PF]` Keyboard shortcut help overlay (`?`) — `App.tsx` · discover shortcuts · I2/C3 · S/low.
60. `[ ][PF]` Ensure error text is programmatically associated with fields — forms · I3/C4 · S/low.

## 4. Performance

61. `[x][PF]` Workspace polls single instance, not all labs — `api/routes_infra.py get_lab_instance`, `pages/LabWorkspace.tsx` (PR #24) · I3/C5 · S/low.
62. `[~][PF]` Visibility-aware polling everywhere — `Running.tsx`, `Dashboard.tsx` done; audit others · I2/C4 · S/low.
63. `[ ][PF]` Adaptive poll backoff when nothing is transitioning — `pages/Running.tsx` · fixed 4s even when idle · I3/C4 · M/low · fast while starting/awaiting-IP, slow when stable.
64. `[~][PF]` Code-split heavy routes — `App.tsx` lazy routes exist; LabWorkspace chunk 300KB (xterm) is unavoidable but could defer addon · I2/C3 · S/low.
65. `[ ][PF]` Cache host LAN IP / capabilities with short TTL — `routes_infra.py _host_lan_ip` runs `ip route` per call · I2/C4 · S/low.
66. `[ ][PF]` Index hot query columns — `FlagSubmission(user_id,flag_id,correct)`, `CourseProgress(user_id)` · verify indexes exist · I3/C3 · S/low.
67. `[ ][PF]` Avoid N+1 in `/api/profiles` list — `profiles/service.py` · 1440 profiles; ensure pagination + single query · I3/C3 · M/low.
68. `[ ][PF]` Debounce the Machines search/filter input — `pages/Machines.tsx` · request per keystroke · I2/C4 · S/low.
69. `[ ][PF]` Gzip/precompress static dist assets — `backend/app/main.py StaticFiles` · serve .gz · I2/C3 · S/low.
70. `[ ][PF]` Memoise rankFor / heavy render computations — `ui.tsx` · minor · I1/C3 · S/low.
71. `[ ][PF]` Batch achievement checks after events — `courses/achievements.py` · recompute cost · I2/C3 · M/low.
72. `[ ][PF]` Stream serial console more efficiently — `vms/libvirt_driver.py`, `routes_ws.py` · verify no busy-loop · I2/C3 · M/med.
73. `[ ][PF]` Lazy-load Swagger UI only on demand — `main.py SWAGGER_DIR` · bundled into dist · I2/C3 · S/low.
74. `[ ][PF]` Paginate `/api/vms` and lab instances for heavy users — `routes_infra.py` · I2/C3 · S/low.
75. `[ ][NY]` Avoid repeated `virsh`/`ip` subprocess spawns in status — `pwnforge-host.sh`, `pwnforge.py` · cache within a status cycle · I2/C3 · M/low.
76. `[ ][PF]` Reuse DB session for IP refresh loop — `routes_infra.py _refresh_ip` per-VM commit · batch · I2/C3 · S/low.
77. `[ ][PF]` Throttle host_stats cpu_percent interval cost — `host_monitor.py` 0.15s blocking per call · cache 2s · I2/C4 · S/low.
78. `[ ][PF]` Prefetch next lesson content on course view — `CourseDetail.tsx` · perceived speed · I2/C3 · S/low.
79. `[ ][PF]` Compress WS console output for slow links — `routes_ws.py` · I1/C2 · M/med.
80. `[ ][PF]` Measure & budget initial JS (currently ~62KB gz index) — add a size check in CI · I2/C3 · S/low.

## 5. Reliability & error handling

81. `[x][PF]` Graceful "lab instance gone" state — `pages/LabWorkspace.tsx` (PR #24) · I3/C5 · S/low.
82. `[ ][PF]` Global React error boundary — `App.tsx` · a render error blanks the app · I4/C4 · S/low.
83. `[ ][PF]` Typed, actionable API error messages — `api/*` HTTPException details · some are terse · I3/C4 · M/low.
84. `[ ][PF]` Retry only failed background steps — `jobs/runner.py` · re-running whole op wastes time · I3/C3 · M/med.
85. `[ ][PF]` Idempotent lab start (no duplicate VMs on double-click) — `labs/service.py` · guard re-entrancy · I3/C4 · M/med.
86. `[ ][PF]` Clear handling of expired WS/session in terminal — `Xterm` · reconnect/notify on close · I3/C4 · M/low.
87. `[ ][PF]` Surface `last_error` prominently with remediation — `Running.tsx`, `Labs.tsx` · shown but terse · I3/C4 · S/low.
88. `[ ][PF]` Health endpoint `/api/health` for liveness — `main.py` · ops/monitoring · I3/C4 · S/low.
89. `[~][PF]` Readiness recompute on startup — `main.py _refresh_readiness` (earlier PR #16) · verify still wired · I3/C4 · S/low.
90. `[ ][PF]` Cleanup orphaned libvirt domains/overlays on boot — `vms/service.py` · drift after crash · I3/C3 · M/med.
91. `[ ][PF]` Transaction safety audit on multi-write endpoints — e.g. `start_vm` · ensure commit/rollback consistent · I3/C3 · M/low.
92. `[ ][NY]` Firewall rules idempotency re-verify — `pwnforge-host.sh write_tailnet_rules` · re-apply safe (done); add a self-test · I3/C4 · S/low.
93. `[ ][NY]` Boot unit failure visibility — `pwnforge-tailnet.service` · surface status in dashboard · I3/C3 · S/low.
94. `[ ][PF]` Guard against clock skew in streak calc — `courses/service.py` streak · `last_active_day` string compare · I2/C3 · S/low.
95. `[ ][PF]` Backpressure / timeout on image fetch — `images/service.py` · hung downloads · I2/C3 · M/low.
96. `[ ][PF]` Validate catalogue reseed is transactional — `catalog/importer.py` · partial import on error · I3/C3 · M/low.
97. `[ ][PF]` WS auth + origin checks — `routes_ws.py` · ensure console WS authenticates the user/owner · I5/C3 · M/med · security-adjacent.
98. `[ ][PF]` Detect & report full disk before VM start — `storage/service.py` · fail early with guidance · I3/C4 · S/low.
99. `[ ][NY]` Graceful degrade when Tailscale absent — `pwnforge-host.sh` · already warns; ensure LAN path still works · I3/C4 · S/low.
100. `[ ][PF]` Consistent 401 handling → redirect to login in SPA — `api.ts req` throws; pages vary · central handler · I3/C4 · S/low.

## 6. Security & auth

101. `[x][PF]` Change-password UI (current+new, reveal toggle) — `pages/Settings.tsx` (this session) · I3/C5 · S/low.
102. `[x][PF]` Password reset does not expose plaintext (hashed) — confirmed `security/crypto.py` · I4/C5 · n/a.
103. `[ ][PF]` Session revocation on password change surfaced to user — `auth/service.py` · tell the user other sessions ended · I3/C4 · S/low.
104. `[ ][PF]` Rate-limit login attempts — `routes_auth.py login` · brute-force protection · I4/C4 · M/low.
105. `[ ][PF]` CSRF protection for cookie-auth POSTs — `api/deps.py` · SameSite + token · I4/C3 · M/med.
106. `[ ][PF]` Account lockout / backoff after N failures — `auth/service.py` · I3/C3 · M/low.
107. `[ ][PF]` Audit log viewer in admin UI — `security/audit.py` records; no UI · I3/C4 · M/low.
108. `[ ][PF]` Secrets never logged — `labs/flags.py` note exists; add a lint/test · I4/C4 · S/low.
109. `[ ][PF]` Enforce strong admin password at bootstrap — `routes_auth.py bootstrap` · min length setting default 1 · I3/C4 · S/low.
110. `[ ][PF]` Two-person/confirm for destructive admin ops — reset/delete all · I2/C3 · M/low.
111. `[ ][NY]` Least-privilege sudo helper audit — `pwnforge-host.sh` via systemd-run · document exact commands · I4/C4 · M/med.
112. `[ ][PF]` Lab target egress stays blocked (verify) — `networks/service.py`, firewall · ensure isolated by default · I5/C4 · M/med · core promise.
113. `[ ][PF]` Signed/stored session TTL enforcement — `deps.py _session_ttl` · verify expiry honored · I3/C3 · S/low.
114. `[ ][PF]` Flag submission server-side only (verify) — `labs/flags.py` · confirm no client leak · I4/C4 · S/low.
115. `[ ][PF]` Role checks on every admin route — audit `routes_admin.py`, `routes_infra.py` · I4/C4 · M/low.
116. `[ ][PF]` Redact secrets in support bundle (item 289) — new · I3/C3 · M/low.
117. `[ ][NY]` Confirm before opening PwnForge to LAN/tailnet — `web/pwnforge.js` has a confirm dialog · verify wording/least-priv · I4/C4 · S/low.
118. `[ ][PF]` Content Security Policy headers — `main.py` · mitigate XSS · I3/C3 · M/low.
119. `[ ][PF]` Derived-secret flags use constant-time compare — `security/crypto.constant_time_equals` used; verify everywhere · I3/C4 · S/low.
120. `[ ][PF]` Password field autocomplete hints correct — `Login.tsx`, change-password · set `current-password`/`new-password` (done in change form) · I2/C4 · S/low.

## 7. Networking & lab access

121. `[x][PF]` Copyable nmap/ssh connect commands per machine — `components/Connect.tsx` (PRs #23/#24) · I4/C5 · S/low.
122. `[x][PF]` Auto-filled host LAN IP + lab CIDR in commands — `routes_infra host_caps`, `Connect.tsx` (PR #24) · I4/C5 · S/low.
123. `[x][PF]` `-Pn` on all suggested scans (targets ignore ping) — `Connect.tsx`, `Guide.tsx` · I3/C5 · S/low.
124. `[x][NY]` Reach labs over LAN and tailnet — `pwnforge-host.sh write_tailnet_rules` (PR #29) · I4/C5 · M/low.
125. `[x][NY]` Route advertisement preserves exit node — `pwnforge-host.sh ts_routes` · I4/C5 · S/low.
126. `[~][NY]` Cross-platform client CLI (`pwnforge` install/status/test/remove) — `web/pwnforge-install-*.sh` (parallel work) · verify, document, test · I4/C3 · M/med.
127. `[ ][PF]` Explain route-approval step inline with a deep link — `Connect.tsx`/`Guide.tsx` link to admin console (done); add status check · I3/C4 · S/low.
128. `[ ][NY]` `pwnforge status` shows active path (tailnet vs LAN) — client CLI · verify output · I3/C3 · S/low.
129. `[ ][NY]` `pwnforge remove` fully reverses routes/helper — client CLI · acceptance: no residual route · I3/C4 · S/low.
130. `[ ][PF]` Per-lab network CIDR in API for precise routes — `_vm_out` lacks `network_cidr`; Connect derives /24 · add field · I2/C4 · S/low.
131. `[ ][PF]` Reachability indicator ("target reachable from you?") — `LabWorkspace.tsx` · ping/TCP check from client is hard; show host-side readiness · I3/C3 · M/med.
132. `[ ][NY]` Idempotent LAN route add on client (don't duplicate) — install script · I3/C4 · S/low.
133. `[ ][NY]` Client yields to approved Tailscale route (no LAN override) — install script · stated requirement · I3/C4 · M/med.
134. `[ ][PF]` Observable firewall state (what's open, to whom) — admin UI panel reading `PWNFORGE-TAILNET` chain via helper · I3/C3 · M/med.
135. `[ ][PF]` One-click "Enable lab access" toggle on dashboard PwnForge page — `NY web/pwnforge.js` → calls host helper · offered earlier, not built · I4/C3 · M/med.
136. `[ ][PF]` IPv6 handling / explicit disable for lab nets — `networks/service.py` · avoid surprises · I2/C2 · M/low.
137. `[ ][NY]` Document route approval with screenshots — `docs/macos.md` · operator clarity · I3/C4 · S/low.
138. `[ ][PF]` Detect overlapping host subnet with lab CIDR — `networks/service.py` · warn if 10.200/16 collides · I3/C3 · S/low.
139. `[ ][PF]` Per-instance connection instructions for Windows client — `Connect.tsx` has route syntax; add full nmap/ssh note for Win · I2/C3 · S/low.
140. `[ ][NY]` Health-check the tailnet route from the host side — `pwnforge-host.sh cmd_tailnet_status` · expand · I3/C3 · S/low.

## 8. VM lifecycle & provisioning

141. `[x][PF]` Real VMs only; no silent simulation in prod — `vms/factory.py _UnavailableDriver` · verify remains · I5/C5 · n/a · core promise.
142. `[x][PF]` arm64 NIC ROM fix (efi-virtio.rom) — `vms/libvirt_driver.py <rom enabled='no'/>` + ipxe-qemu · I4/C5 · S/low.
143. `[ ][PF]` Preflight resource estimate before VM start — `vms/service.py` · "needs 1GB RAM, host has X" · I4/C4 · M/low.
144. `[ ][PF]` Bulk start/stop/cleanup with affected-machine preview — `pages/Running.tsx` stopAll exists; add preview · I3/C4 · M/low.
145. `[ ][PF]` Safe lab snapshots with storage cost shown — `vms/service.snapshot_create` exists; surface in UI · I3/C3 · M/low.
146. `[ ][PF]` Disposable vs persistent clearly labelled + policy — `Running.tsx` shows flags; explain lifecycle · I2/C4 · S/low.
147. `[ ][PF]` Auto-stop idle lab VMs after TTL — `jobs/` · reclaim RAM · I4/C3 · M/med · opt-in.
148. `[ ][PF]` Show provisioning phase (creating→booting→IP) — `_vm_out status` is coarse · granular states · I3/C3 · M/low.
149. `[ ][PF]` Real-VM readiness panel before workspace opens — `LabWorkspace.tsx` · health/addr/connect before entering · I3/C4 · M/low.
150. `[ ][PF]` Role-image build progress surfaced — `images/service.py build` · long, opaque · I3/C3 · M/low.
151. `[ ][PF]` Reboot/reset confirm with data-loss note — `Running.tsx` reset · disposable implications · I2/C4 · S/low.
152. `[ ][PF]` Reclaim overlay disk on VM delete (verify) — `vms/service.delete_instance` · avoid leak · I3/C3 · S/low.
153. `[ ][PF]` Cap concurrent VMs by host RAM — `vms/service.py` · prevent OOM · I4/C3 · M/med.
154. `[ ][PF]` Serial console scrollback buffer — `Xterm` · lost output on reconnect · I2/C3 · M/low.
155. `[ ][PF]` Per-machine resource usage (live) — `host_monitor.py` has per-pid; map to VMs · I3/C3 · M/med.
156. `[ ][PF]` Graceful shutdown vs destroy choice — `vms/service.stop_instance force` · expose both clearly · I2/C3 · S/low.
157. `[ ][PF]` Image integrity verify before use — `images/service` verify endpoint exists; auto-run · I3/C3 · S/low.
158. `[ ][PF]` Cloud-init seed build errors surfaced — `vms/provision.py` · opaque failures · I3/C3 · M/low.
159. `[ ][PF]` Lab teardown removes isolated network + firewall — `networks/service.py` · no residue · I3/C3 · M/low.
160. `[ ][PF]` Warn when host virt disabled in BIOS — `core/host_monitor`/`doctor` · actionable · I3/C4 · S/low.

## 9. Learning paths & courses

161. `[x][PF]` Every learning path references real labs/machines — `catalog/content/paths.py` (this session) · I4/C5 · M/low.
162. `[x][PF]` Path steps show friendly lab titles + difficulty — `learning_paths/service.py` (this session) · I3/C5 · S/low.
163. `[x][PF]` Continue-to-next-course button — `CourseDetail.tsx`/`PathDetail.tsx` (earlier PR #20) · I3/C5 · S/low.
164. `[ ][PF]` Explain locked steps (prereq map) — `PathDetail.tsx` shows "locked"; add why + shortest unlock · I3/C4 · M/low.
165. `[ ][PF]` Goal-based recommendations with rationale — `pages/Dashboard.tsx recs` show reasons; deepen "what it unlocks" · I3/C3 · M/low.
166. `[ ][PF]` Lesson outcomes/time/prereqs before start — `CourseDetail.tsx` · set expectations · I3/C4 · S/low.
167. `[ ][PF]` Explain missing lab prereqs on a path (host can't run it) — `PathDetail.tsx` + readiness · I3/C3 · M/low.
168. `[ ][PF]` Competency → evidence linking — `UserCompetency` + `pages/Skills.tsx` · show what earned each · I3/C3 · M/low.
169. `[ ][PF]` Reliable resume to last lesson/answer — `CourseDetail.tsx` + `LessonProgress` · I3/C4 · M/low.
170. `[ ][PF]` Autosaved notes/command history per lesson — new table · I3/C3 · M/med.
171. `[x][PF]` Black-box labs with tiered hints + gated walkthrough — `catalog/content/labs.py` (earlier) · I4/C5 · M/low.
172. `[x][PF]` Case-insensitive flag answers — `security/crypto.hash_flag` lower/strip · I3/C5 · S/low.
173. `[ ][PF]` Expert-tier content to reach path difficulty_max — courses top out "advanced"; several paths claim "expert" · I4/C3 · L/med · content work.
174. `[ ][PF]` Path progress bar counts required vs optional clearly — `learning_paths/service.py percent` counts all steps · clarify · I3/C4 · S/low.
175. `[ ][PF]` Search/filter the 89-course catalogue by competency — `pages/Courses.tsx` · I3/C3 · M/low.
176. `[ ][PF]` Lab "objectives → done" checklist in workspace — `LabWorkspace.tsx` shows objectives; make them checkable · I3/C3 · M/low.
177. `[ ][PF]` Course bookmarks/notes (item 231) — new · I2/C3 · M/low.
178. `[ ][PF]` Suggest the next lab after solving one — `flags.submit_flag` success → recommend · I3/C3 · S/low.
179. `[ ][PF]` Difficulty legend/explanation — `ui.tsx Diff` chips · define beginner..expert · I2/C4 · S/low.
180. `[ ][PF]` Lab reset keeps flag validity (re-derive) — `provision.derive_flag` per instance · verify on reset · I3/C3 · S/low.

## 10. Assessment & progress integrity

181. `[x][PF]` Assessment XP idempotent (no double award) — `courses/service.py xp_awarded` guard · verify retries/refresh · I4/C5 · S/low · acceptance test exists.
182. `[ ][PF]` Idempotency test for repeat quiz submissions — `backend/tests` · lock in behavior · I3/C4 · S/low.
183. `[ ][PF]` Server-authoritative quiz scoring (no client trust) — `courses/service.py` answer_hash · verify · I4/C4 · S/low.
184. `[ ][PF]` Prevent XP farming via hint reveal — `service.py reveal hint` · ensure no XP · I3/C3 · S/low.
185. `[ ][PF]` Assessment feedback explains missed concepts — `CourseDetail.tsx` · without exposing keys early · I3/C3 · M/low.
186. `[ ][PF]` Partial-progress save mid-assessment — `AssessmentProgress` · resume · I3/C3 · M/low.
187. `[ ][PF]` Flag submission idempotent crediting — `labs/flags.py already` path · verify · I3/C4 · S/low.
188. `[ ][PF]` Achievement award idempotent — `courses/achievements.py` + `UserAchievement` unique · verify · I3/C4 · S/low.
189. `[ ][PF]` XP recalculation/repair tool — admin CLI · fix drift · I2/C3 · M/low.
190. `[ ][PF]` Streak logic unit tests — `courses/service.py` · edge cases (TZ, gaps) · I2/C3 · S/low.
191. `[ ][PF]` Audit XP sources sum ≤ theoretical max — report · detect bugs · I2/C3 · S/low.
192. `[ ][PF]` Certificate issuance idempotent — `learning_paths/service.issue_if_complete` unique(user,path) · verify · I3/C4 · S/low.
193. `[ ][PF]` Prevent cert for incomplete after content changes — adding steps lowers %; handle gracefully · I3/C3 · M/low.
194. `[ ][PF]` Quiz attempt history per user — new · analytics/resume · I2/C3 · M/low.
195. `[ ][PF]` Time-limited assessments (optional) — `service.py` · I1/C2 · M/med.
196. `[ ][PF]` Randomised question order (anti-share) — importer/service · I2/C2 · M/low.
197. `[ ][PF]` Progress export (JSON) for the learner — new endpoint · I2/C3 · S/low.
198. `[ ][PF]` Consistent "completed" definition across course/lab steps — `learning_paths/service.py` · doc + test · I3/C3 · S/low.
199. `[ ][PF]` Guard double-award when two tabs submit — DB unique/locking · I3/C3 · M/low.
200. `[ ][PF]` Assessment answer hashing salt review — `crypto.hash_answer` · I2/C3 · S/low.

## 11. Account & progress data

201. `[x][PF]` Account reset clears learner state, keeps account — `routes_auth.account/reset` (this session) · I4/C5 · S/low.
202. `[x][PF]` Reset is consistent across all progress tables — includes lesson/assessment/competency/flags/ach/cert · I4/C5 · S/low.
203. `[ ][PF]` Reset confirmation lists exactly what is kept/removed — `Settings.tsx AccountReset` text present; add an itemised modal · I3/C4 · S/low.
204. `[ ][PF]` Reset does not touch running VMs (verify + state in text) — stated; add a test · I3/C4 · S/low.
205. `[ ][PF]` Admin reset of another user's progress — `routes_admin.py` · support/ops · I2/C3 · M/low.
206. `[ ][PF]` Export my data (GDPR-style) — new endpoint · I2/C3 · M/low.
207. `[ ][PF]` Delete my account (self-service, admin-guarded) — `routes_auth.py` · I2/C3 · M/med.
208. `[ ][PF]` Display name vs username editable in profile — `User.display_name` · no profile UI · I2/C3 · S/low.
209. `[ ][PF]` Preferred specialization editable — `User.preferred_specialization` · affects recs · I2/C3 · S/low.
210. `[ ][PF]` Per-user settings (theme/notifications) persisted server-side — currently localStorage · I2/C3 · M/low.
211. `[ ][PF]` Reset confirmation requires typing username — reduce accidents · I2/C4 · S/low.
212. `[ ][PF]` Audit record for account.reset (done) surfaced to admin — `audit.py` · I2/C3 · S/low.
213. `[ ][PF]` Soft-delete / recovery window for reset — snapshot before wipe · I2/C2 · M/med.
214. `[ ][PF]` Progress summary before reset ("you'll lose X") — compute counts · I3/C3 · S/low.
215. `[ ][PF]` Multi-user roster view for admins — `routes_admin.py` · I2/C3 · M/low.
216. `[ ][PF]` Password change forces re-login everywhere (verify + tell) — `auth/service.py` · I3/C3 · S/low.
217. `[ ][PF]` Session list + revoke individual sessions — `UserSession` table · I3/C3 · M/low.
218. `[ ][PF]` Email (optional) for recovery — `User.email` exists; wire recovery · I2/C2 · L/med.
219. `[ ][PF]` Consistent timestamps in local time + UTC inspect — only 5 toLocaleString usages · standardise · I3/C4 · S/low.
220. `[ ][PF]` "Last active" shown on profile — `User.last_active_day/last_login_at` · I1/C3 · S/low.

## 12. Updates & recovery

221. `[~][PF]` In-app Update button with truthful output — `pages/Settings.tsx Updates`, `core/updater.py` · verify streams real stdout + failure state · I4/C4 · M/low.
222. `[ ][PF]` Pre-update backup + visible backup status — `cli.py backup` exists; link into update flow · I4/C4 · M/low · core promise.
223. `[ ][PF]` Clear recovery path if update fails — `updater.py` · rollback/guide · I4/C3 · M/med.
224. `[ ][PF]` Show current vs available version + release notes — `routes_admin version` shows branch · add remote compare · I3/C3 · M/low.
225. `[ ][PF]` Update preserves user data (verify migrations idempotent) — `migrations/` inspect-first pattern · test · I4/C4 · M/low.
226. `[ ][PF]` Dry-run update (show commands, no apply) — `scripts/update.sh` · I3/C3 · S/low.
227. `[ ][PF]` Update lock (prevent concurrent updates) — `updater.py` · I3/C3 · S/low.
228. `[ ][PF]` Post-update readiness recheck + report — ties to `_refresh_readiness` · I3/C3 · S/low.
229. `[ ][NY]` Dashboard "Update PwnForge" surfaces host log tail — `web/pwnforge.js` · truthful output · I3/C3 · M/low.
230. `[ ][PF]` Backup verification (restore test) — `cli.py backup` "verified"; document restore · I3/C3 · M/low.

## 13. Personalization & deluxe

231. `[ ][PF]` Private bookmarks + notes on courses/lessons/lab steps — new table · I3/C3 · M/med.
232. `[ ][PF]` Portable certificates w/ verification page — `Certificates.tsx` has verify link; build public verify view · I3/C3 · M/low.
233. `[ ][PF]` Privacy-preserving cert sharing (opaque serial) — `learning_paths verify_certificate` · I2/C3 · S/low.
234. `[ ][PF]` Preference sync across devices (opt-in) — server settings · I2/C2 · M/med.
235. `[ ][PF]` Resource usage page w/ trends + cleanup recs — `host_monitor` + storage · I3/C3 · M/med.
236. `[ ][PF]` Per-user reminders + quiet hours — notifications · I2/C2 · M/med.
237. `[ ][PF]` Contextual help drawer on each page — docs/ content · I3/C3 · M/low.
238. `[ ][PF]` Searchable in-app FAQ — reuse `docs/` · I2/C3 · M/low.
239. `[ ][PF]` Favourite/compare machine profiles — `Machines.tsx` · I2/C3 · M/low.
240. `[ ][PF]` Dark/light aware certificate theme — `Certificates.tsx` print CSS present · I1/C3 · S/low.
241. `[ ][PF]` Achievement showcase on profile — `Achievements.tsx` · I2/C3 · S/low.
242. `[ ][PF]` Leaderboard (opt-in, privacy-safe) — new · I2/C2 · M/med.
243. `[ ][PF]` Custom lab start parameters (RAM/vCPU within limits) — `vms` · I2/C3 · M/med.
244. `[ ][PF]` Export certificate as PDF directly (not just print) — `Certificates.tsx` · I2/C3 · S/low.
245. `[ ][PF]` Shareable path progress snapshot — new · I1/C2 · M/low.
246. `[ ][NY]` Music module polish (already: likes/newest sort, 300 cap) — `music.py`/`music.js` · minor UX · I1/C3 · S/low.
247. `[ ][PF]` Theme accent customization — `index.css` tokens · I1/C2 · S/low.
248. `[ ][PF]` Per-learner dashboard vs operator dashboard — `Dashboard.tsx` · role-aware tiles · I3/C3 · M/low.
249. `[ ][PF]` "What's new" changelog surfaced in-app — `docs/` · I2/C3 · S/low.
250. `[ ][PF]` Keyboard-first learner mode — a11y + shortcuts · I2/C2 · M/low.

## 14. Documentation & help

251. `[x][PF]` In-app connection Guide page — `pages/Guide.tsx` (PRs #23/#24) · I4/C5 · M/low.
252. `[~][PF]` Lab-client README (placeholder IP, not real host) — `README.md` (sanitised this session) · I3/C5 · S/low.
253. `[ ][PF]` Keep docs/ in sync with new endpoints — `docs/API.md` · add `/lab-instances/{id}`, `/account/reset`, `host_caps` fields · I3/C4 · S/low.
254. `[ ][NY]` Document the client CLI commands + removal — `docs/macos.md`, nodeyard README · I3/C4 · S/low.
255. `[ ][PF]` Troubleshooting: "Host seems down" → use -Pn — `docs/TROUBLESHOOTING.md` · I3/C4 · S/low.
256. `[ ][PF]` Document rank thresholds + XP economy — `docs/USER_GUIDE.md` · I2/C3 · S/low.
257. `[ ][PF]` Document account reset scope precisely — `docs/USER_GUIDE.md` · I2/C4 · S/low.
258. `[ ][PF]` Security doc: lab isolation + egress policy — `docs/SECURITY.md` · I3/C4 · S/low.
259. `[ ][PF]` Admin doc: update/backup/recovery runbook — `docs/ADMINISTRATION.md`/`BACKUPS.md` · I3/C3 · S/low.
260. `[ ][PF]` Contributing/AGENTS guide for repo conventions — none exists · I3/C3 · S/low.
261. `[ ][PF]` Inline help tooltips for settings keys — `Settings.tsx` descriptions present; link docs · I2/C4 · S/low.
262. `[ ][NY]` Architecture doc update for tailnet/LAN access — `docs/architecture.md` · I2/C3 · S/low.
263. `[ ][PF]` Learning-paths authoring doc reflects lab steps — `docs/LEARNING_PATHS.md` · I2/C3 · S/low.
264. `[ ][PF]` Profile authoring doc examples current — `docs/PROFILE_AUTHORING.md` · I2/C2 · S/low.
265. `[ ][PF]` Screenshot the connection flow in docs — `docs/` · I2/C3 · S/low.
266. `[ ][PF]` FAQ: real vs simulated VMs policy — `docs/` · I3/C4 · S/low.
267. `[ ][NY]` FAQ: route approval + why — `docs/faq.md` · I3/C4 · S/low.
268. `[ ][PF]` Document WS endpoints + auth — `docs/API.md` · I2/C3 · S/low.
269. `[ ][PF]` Changelog file maintained per release — repo root · I2/C3 · S/low.
270. `[ ][PF]` Example `.env` / data-dir doc — `docs/INSTALLATION.md` · I2/C3 · S/low.

## 15. Observability & developer workflow

271. `[ ][PF]` Structured request logging (method/path/status/ms) — `main.py` middleware · I3/C3 · S/low.
272. `[ ][PF]` `/api/health` + `/api/version` for monitoring — `main.py`/`routes_admin` · I3/C4 · S/low.
273. `[ ][PF]` Metrics endpoint (Prometheus) — new · ops · I2/C2 · M/low.
274. `[ ][PF]` One-click redacted support bundle — diagnostics minus secrets/PII · I3/C3 · M/low.
275. `[ ][PF]` CI: run backend pytest + frontend tsc/build — no CI config present · I4/C4 · M/low.
276. `[ ][PF]` Frontend unit/component tests (none today) — add vitest + a few tests · I3/C3 · M/low.
277. `[ ][PF]` Lint/format config enforced (ruff/eslint/prettier) — verify + CI · I2/C3 · S/low.
278. `[ ][PF]` Pre-commit hook for secrets scan — avoid IP/credential leaks (cf. README fix) · I3/C4 · S/low.
279. `[ ][PF]` Type coverage for API responses (pydantic models) — some endpoints return dicts · I2/C3 · M/low.
280. `[ ][PF]` Seed/fixture reset is deterministic + fast — `init --no-profiles` used in tests · I2/C3 · S/low.
281. `[ ][PF]` Test for real-virt capacity gating (env-gated) — two tests fail only on low-RAM dev machines · mark/skip cleanly · I2/C3 · S/low.
282. `[ ][PF]` Dev launch config documented (`.claude/launch.json`) — exists; document · I1/C3 · S/low.
283. `[ ][NY]` Lint shell scripts (shellcheck) — `pwnforge-host.sh`, install scripts · I3/C3 · S/low.
284. `[ ][NY]` Smoke test for `pwnforge-host.sh` subcommands — `bash -n` + dry runs · I3/C3 · M/low.
285. `[ ][PF]` Error tracking hook (optional, self-hosted) — frontend/back · I2/C2 · M/low.
286. `[ ][PF]` Log rotation / journald caps documented — ops · I2/C3 · S/low.
287. `[ ][PF]` Build reproducibility (pin versions) — `requirements.txt`, `package-lock` · I2/C3 · S/low.
288. `[ ][PF]` API contract tests (schema snapshots) — `tests/` · I2/C3 · M/low.
289. `[ ][PF]` Support bundle redaction test — ensure no secrets · I3/C3 · S/low.
290. `[ ][PF]` Performance regression check on bundle size — CI · I2/C3 · S/low.
291. `[ ][PF]` Observability for job runner (queue depth, failures) — `jobs/runner.py` · I3/C3 · M/low.
292. `[ ][PF]` Audit-log retention policy + pruning — `audit.py` · I2/C3 · S/low.
293. `[ ][PF]` DB migration test (upgrade/downgrade on sample) — `migrations/` · I3/C3 · M/low.
294. `[ ][PF]` Feature flags for risky new UI — `settings_service` · I2/C2 · M/low.
295. `[ ][NY]` Dashboard log viewer hides secrets (verify) — `pwnforge.js:139` claims; add a test · I3/C4 · S/low.
296. `[ ][PF]` Health of background readiness task observable — `main.py _refresh_readiness` · I2/C3 · S/low.
297. `[ ][PF]` Request ID correlation across logs — middleware · I2/C2 · S/low.
298. `[ ][PF]` Graceful shutdown drains jobs — `jobs/runner.py` · I2/C3 · M/low.
299. `[ ][PF]` Document test commands in README — `README.md` · I2/C4 · S/low.
300. `[ ][PF]` Nightly catalogue import validation (no broken refs) — importer self-check for dangling course/lab ids in paths · I3/C4 · S/low.

---

## Top ten highest-value candidates (★)

1. **#112 [PF] Verify lab-target egress stays blocked by default** — core safety promise; a regression would let practice boxes reach the internet/other labs. (I5/C4)
2. **#97 [PF] Authenticate & authorize console WebSockets** — ensure `/api/ws/console/*` only serves the owning user; high security impact. (I5/C3)
3. **#222 [PF] Pre-update backup + visible backup status + recovery path** — protects user data across updates; the update flow is a known expectation. (#221–#225) (I4/C4)
4. **#143/#153 [PF] VM preflight resource estimate + concurrent-VM cap** — prevents host OOM when learners start several real VMs. (I4/C3)
5. **#41–#44 [PF] Accessibility baseline** (aria labels, live regions, skip link) — only ~12 aria/role attributes exist today; broad user impact, low risk. (I4/C5)
6. **#104 [PF] Login rate-limiting / lockout** — brute-force protection for a self-hosted, LAN/tailnet-exposed login. (I4/C4)
7. **#173 [PF] Expert-tier content** — several paths advertise `difficulty_max: expert` but courses stop at "advanced"; closes a promised-vs-actual gap. (I4/C3)
8. **#63 [PF] Adaptive polling backoff on Running** — cut idle request load ~2.5× with no behavior change. (I3/C4)
9. **#82 [PF] Global React error boundary** — a single render error currently blanks the whole SPA. (I4/C4)
10. **#253 [PF] Sync docs/API.md with new endpoints** — `/lab-instances/{id}`, `/account/reset`, `host_caps` fields are undocumented. (I3/C4)
