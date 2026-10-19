# UX & "premium feel" backlog — 200 improvements (PwnForge frontend)

Grounded in `frontend/src` (React + Tailwind + custom tokens in `index.css`).
Goal: make the app friendlier and feel more premium without a redesign.
`[x]` = implemented in the premium-polish pass; `[~]` = partial; `[ ]` = open.

---

## A. Motion & micro-interactions
1. `[x]` Shimmer skeleton loaders replacing bare spinners on data pages — `ui.tsx Skeleton`, pages.
2. `[x]` Animated progress-bar fill (width transition) — `.bar > i`.
3. `[x]` Respect `prefers-reduced-motion` globally — `index.css`.
4. `[x]` Default subtle card hover-lift + glow on interactive cards — `.card-hover`.
5. `[ ]` Count-up animation for XP / stat numbers — `ui.tsx Stat`, Dashboard.
6. `[ ]` Ring progress animates from 0 on mount — `ui.tsx Ring`.
7. `[ ]` Page/route transition fade (enter/leave) — `App.tsx` + `framer`-free CSS.
8. `[ ]` Button press "squish" with spring easing — `.btn:active`.
9. `[ ]` Primary button hover sheen/gradient sweep — `.btn-primary`.
10. `[ ]` Toast slide/stack animation polish — generalise `ach-toast-in`.
11. `[ ]` Hover elevation on list rows (Running/Machines) — subtle bg + shadow.
12. `[ ]` Icon button hover scale (1.0→1.08) — `icons.tsx` wrappers.
13. `[ ]` Tab underline slides between tabs — `ui.tsx Tabs`.
14. `[ ]` Smooth expand/collapse for hints & setup guides — `LabWorkspace`, `Connect`.
15. `[ ]` Copy-success check animation (scale/tick) — reusable `CopyButton`.
16. `[ ]` Confetti / glow burst on flag capture & cert earn — `LabWorkspace`, `Certificates`.
17. `[ ]` Streak flame subtle pulse — `Dashboard`.
18. `[ ]` Skeleton→content crossfade — `Skeleton`.
19. `[ ]` Sidebar active-item indicator slides — `App.tsx Sidebar`.
20. `[ ]` Loading bar at top on navigation/async — `App.tsx`.

## B. Typography & spacing
21. `[x]` Tabular numerals for stats/metrics so digits don't jitter — `.tnum`.
22. `[ ]` Consistent heading scale across pages — audit `text-2xl`/`text-xl`.
23. `[ ]` Tighten line-height on dense tables/lists — `Running`, `Machines`.
24. `[ ]` Max-width reading measure on prose/guide — `.prose-body`, `Guide`.
25. `[ ]` Consistent page header component (title + subtitle + actions) — new `PageHeader`.
26. `[ ]` Larger, calmer empty-state typography — `ui.tsx Empty`.
27. `[ ]` Balance long titles with `text-wrap: balance` — headings.
28. `[ ]` Monospace alignment for IPs/commands — ensure `.mono` everywhere.
29. `[ ]` Section label style unified (uppercase/tracking) — reuse across pages.
30. `[ ]` Consistent vertical rhythm (space-y scale) — audit `space-y-*`.
31. `[ ]` Truncation with tooltip for long names — `Running`, `Labs`.
32. `[ ]` Avoid all-caps where it hurts readability — review chips/labels.
33. `[ ]` Numeric right-alignment in metric columns — tables.
34. `[ ]` Consistent button label casing — sentence case.
35. `[ ]` Larger tap text on mobile (min 14px) — responsive.
36. `[ ]` Caption/footnote text token — small muted usage.
37. `[ ]` Code/inline-code consistent sizing — `.prose-body code` vs `.doc code`.
38. `[ ]` Avoid orphaned single words in subtitles — balance.
39. `[ ]` Proper ellipsis for multi-line clamp — `-webkit-line-clamp`.
40. `[ ]` Consistent spacing inside cards (p-4/p-5) — audit.

## C. Color, depth & theming
41. `[x]` Soft layered shadow/elevation token for cards — `--elev`.
42. `[ ]` Smooth theme switch transition (bg/color) — `html` transition.
43. `[ ]` High-contrast theme option — `data-theme="contrast"`.
44. `[ ]` Accent-color personalization — token override in Settings.
45. `[ ]` Status colors consistent (ok/warn/bad) across chips/rings — audit.
46. `[ ]` Subtle noise/grain texture on hero — premium depth.
47. `[ ]` Gradient accents on key CTAs only (avoid overuse) — review.
48. `[ ]` Dark-mode-aware glow intensity — reduce bloom in light.
49. `[ ]` Consistent border tokens (`--line`/`--line2`) usage — audit.
50. `[ ]` Focus ring color matches brand in both themes — done via `--brand`.
51. `[ ]` Panel hover surface token consistency — `--panel3`.
52. `[ ]` Selection color in light theme tuned — `::selection`.
53. `[ ]` Chart/metric palette accessible (not color-only) — `Dashboard`.
54. `[ ]` Rank colors legible on panel bg — contrast check.
55. `[ ]` Reduce pure-black/white; use tokens — audit.
56. `[ ]` Scrollbar styled in light theme too — `::-webkit-scrollbar`.
57. `[ ]` Elevation increases on hover (lift + shadow) — `.card-lift`.
58. `[ ]` Divider/hairline consistency — `.hairline`.
59. `[ ]` Brand glow on primary focus states — inputs/buttons.
60. `[ ]` Themeable success/danger surfaces for callouts — `.callout-*`.

## D. Feedback, notifications & status
61. `[ ]` App-wide toast system (success/error/info) — new `Toast` provider.
62. `[ ]` Replace inline `setMsg` strings with toasts — Settings/Labs/Running.
63. `[ ]` Optimistic UI with rollback on failure — actions.
64. `[ ]` Inline field validation with helpful messages — forms.
65. `[ ]` Consistent "saved!" confirmation — Settings.
66. `[ ]` Undo toast for reversible actions (stop/delete) — Running.
67. `[ ]` Notification inbox (severity, time, links) — new.
68. `[ ]` Live job progress with elapsed time — `Settings Updates`, jobs.
69. `[ ]` Clear error states with retry buttons — API failures.
70. `[ ]` Copy feedback unified (tick + "Copied") — `CopyButton`.
71. `[ ]` Destructive actions use consistent confirm pattern — AccountReset style.
72. `[ ]` Disabled buttons explain why (tooltip) — gated actions.
73. `[ ]` Status pills with icon + text (not color-only) — chips.
74. `[ ]` WS connect/disconnect toast in terminal — `LabWorkspace`.
75. `[ ]` Flag-correct celebratory feedback — `LabWorkspace`.
76. `[ ]` Form submit spinners on buttons (not page) — all forms.
77. `[ ]` Network-offline banner — global.
78. `[ ]` Rate-limit/lockout friendly messaging — Login.
79. `[ ]` Success/first-time nudges (e.g., "try a lab") — Dashboard.
80. `[ ]` Consistent toast position + max stack — provider.

## E. Loading & empty states
81. `[x]` Dashboard skeleton (hero + stats + rings) — `Dashboard`.
82. `[ ]` Courses/Machines list skeletons — pages.
83. `[x]` Richer `Empty` component (icon + text + action) — `ui.tsx Empty`.
84. `[ ]` Per-widget loading (not whole page) — Dashboard tiles.
85. `[ ]` Skeleton for lab workspace while instance loads — `LabWorkspace`.
86. `[ ]` Empty states link to the action that fills them — Running/Certs.
87. `[ ]` Shimmer for table rows — Running/Machines.
88. `[ ]` Lazy image/asset placeholders — where applicable.
89. `[ ]` "No results" vs "nothing yet" differentiated — search/empty.
90. `[ ]` Retry affordance on failed loads — pages.
91. `[ ]` Progressive content reveal (stagger) — lists.
92. `[ ]` Keep layout stable (reserve space) to avoid shift — skeletons.
93. `[ ]` Spinner only for sub-second micro-waits — buttons.
94. `[ ]` Empty achievements/certs encouraging copy — pages.
95. `[ ]` Skeleton respects reduced-motion (static) — `Skeleton`.
96. `[ ]` First-load splash with brand mark — optional.
97. `[ ]` Cached last-known data while refreshing — Running/Dashboard.
98. `[ ]` Error boundary card is on-brand — ties to #82 (shipped).
99. `[ ]` Empty lab catalogue guidance (host setup) — Labs.
100. `[ ]` Loading copy varies by context — friendly microcopy.

## F. Navigation & wayfinding
101. `[ ]` Command palette (Cmd-K) — new.
102. `[ ]` Global search across content — new.
103. `[ ]` Breadcrumbs preserving filters — `App.tsx`.
104. `[ ]` Active route highlight polish — Sidebar (has indicator).
105. `[ ]` Keyboard shortcut help (`?`) overlay — new.
106. `[ ]` Back button that remembers scroll — router.
107. `[ ]` Running count badge in sidebar — `App.tsx`.
108. `[ ]` Sticky page header with actions — `PageHeader`.
109. `[ ]` Quick-switch between labs/machines — header dropdown.
110. `[ ]` Recently viewed list — Dashboard.
111. `[ ]` Pin/favourite items — new.
112. `[ ]` Deep links to lab workspace tabs — `LabWorkspace`.
113. `[ ]` Consistent "open in new context" affordances — links.
114. `[ ]` Mobile nav drawer — responsive sidebar.
115. `[ ]` Section anchors in long docs/guide — `Guide`.
116. `[ ]` Next/prev lesson nav — `CourseDetail`.
117. `[ ]` Path step → lab deep link (not just /labs) — `PathDetail`.
118. `[ ]` Keyboard list navigation (arrow keys) — lists.
119. `[ ]` Persistent filters in URL query — Machines.
120. `[ ]` "Jump to top" on long pages — util.

## G. Forms & inputs
121. `[ ]` Password show/hide everywhere — done in change-password; extend Login.
122. `[ ]` Inline password strength meter — Login/bootstrap.
123. `[ ]` Flag input: trim + submit on Enter + clear feedback — `LabWorkspace`.
124. `[ ]` Autofocus first field on forms — Login/dialogs.
125. `[ ]` Field-level validation messages — forms.
126. `[ ]` Consistent input sizing/padding — `.input`.
127. `[ ]` Select menus styled to match theme — `select`.
128. `[ ]` Settings: typed controls (toggle/number/select) per key — `Settings`.
129. `[ ]` Debounced search inputs — Machines/Courses.
130. `[ ]` Clearable inputs (x button) — search fields.
131. `[ ]` Copyable read-only fields (API base, serials) — Settings/Certs.
132. `[ ]` Numeric steppers for vCPU/RAM — VM params.
133. `[ ]` Keyboard-accessible toggles — Settings bools.
134. `[ ]` Form dirty-state + leave warning — Settings.
135. `[ ]` Submit disabled until valid, with reason — forms.
136. `[ ]` Error summary at top of long forms — Settings.
137. `[ ]` Autocomplete attributes correct — Login/change-pw (done).
138. `[ ]` Placeholder vs label distinction — a11y.
139. `[ ]` Success state on save (checkmark) — Settings.
140. `[ ]` Consistent button order (primary right) — dialogs.

## H. Data display & tables
141. `[ ]` Sortable columns on Machines/Running — tables.
142. `[ ]` Column visibility toggles — Machines.
143. `[ ]` Sticky table headers — long lists.
144. `[ ]` Zebra/row hover for scannability — tables.
145. `[ ]` Compact/comfortable density toggle — tables.
146. `[ ]` Inline status chips with icons — Running.
147. `[ ]` Relative + absolute time (local, UTC on hover) — all timestamps.
148. `[ ]` Human-readable sizes/durations — storage/uptime.
149. `[ ]` Empty cells show "—" consistently — tables.
150. `[ ]` Row actions in a kebab menu — Running/Machines.
151. `[ ]` Bulk-select with action bar — Running.
152. `[ ]` Pagination / virtualied long lists — Machines (1440).
153. `[ ]` Copy row value (IP, id) inline — Running.
154. `[ ]` Group by lab / network — Running.
155. `[ ]` Metric trend sparklines — resource page.
156. `[ ]` Progress shown as both % and fraction — paths.
157. `[ ]` Tooltips on truncated/abbreviated values — tables.
158. `[ ]` Consistent id formatting (short + copy) — VM/lab ids.
159. `[ ]` Status legend where colors used — Dashboard.
160. `[ ]` Export table to CSV — Machines/Running.

## I. Lab & terminal experience
161. `[ ]` Terminal font-size control + persistence — `Xterm`.
162. `[ ]` Terminal reconnect button on disconnect — `Xterm`.
163. `[ ]` Copy/paste helpers + right-click menu — `Xterm`.
164. `[ ]` Fullscreen terminal toggle — `LabWorkspace`.
165. `[ ]` Per-machine quick actions (scan/ssh) prefilled — `Connect` (partly done).
166. `[ ]` Target readiness panel before entering workspace — `LabWorkspace`.
167. `[ ]` Objective checklist that ticks off — `LabWorkspace`.
168. `[ ]` Hint reveal with cost/consequence clarity — `LabWorkspace`.
169. `[ ]` Walkthrough formatted (not raw pre) — `LabWorkspace` guide.
170. `[ ]` Live IP copy + "open in terminal" hint — `LabWorkspace`.
171. `[ ]` Network topology mini-diagram — `LabWorkspace`.
172. `[ ]` Session timer / lab elapsed time — `LabWorkspace`.
173. `[ ]` Flag format hint + example — `LabWorkspace`.
174. `[ ]` Terminal theme matches app theme — `Xterm`.
175. `[ ]` Keyboard shortcut to focus terminal — `LabWorkspace`.
176. `[ ]` Machine status transitions animated — `Running`/`LabWorkspace`.
177. `[ ]` Clear "target vs practice box" visual language — `LabWorkspace` (partly).
178. `[ ]` Reconnect preserves scrollback — `Xterm`.
179. `[ ]` Accessible non-terminal fallback for key tasks — a11y.
180. `[ ]` Lab notes scratchpad — new.

## J. Delight & premium extras
181. `[ ]` Polished certificate design + seal + verify QR — `Certificates`.
182. `[ ]` Achievement showcase wall with rarity — `Achievements`.
183. `[ ]` Rank-up celebration moment — `ui.tsx` + toast.
184. `[ ]` Personalised greeting by time of day — `Dashboard`.
185. `[ ]` Progress "story" / recap view — new.
186. `[ ]` Subtle sound cues (opt-in) — events.
187. `[ ]` Keyboard-driven power-user mode — global.
188. `[ ]` Themed loading microcopy / tips — loaders.
189. `[ ]` Confetti on path completion — `PathDetail`.
190. `[ ]` Shareable progress card (image) — new.
191. `[ ]` "What's new" changelog modal — new.
192. `[ ]` Favicon/tab title reflects running labs — `App.tsx`.
193. `[ ]` Branded empty/error illustrations — assets.
194. `[ ]` Dashboard widget customization — `Dashboard`.
195. `[ ]` Smooth number formatting (k/M) — stats.
196. `[ ]` Premium hover cards (preview on hover) — courses/labs.
197. `[ ]` Consistent iconography set + weights — `icons.tsx`.
198. `[ ]` Onboarding confetti / first-win moment — onboarding.
199. `[ ]` Elegant print styles beyond certs — reports.
200. `[ ]` Polished 404 / error pages on-brand — routing.

---

## Implemented in this pass (premium-polish PR)
Shimmer **skeleton loaders** (A1/E81/E83), **animated progress bars** (A2),
**reduced-motion** support (A3), default **card hover-lift + glow** (A4/C57),
**tabular numerals** for metrics (B21), a **soft elevation token** (C41),
a richer **Empty** state (B26/E83), and a reusable **CopyButton** with tick
feedback (A15/D70). See the premium-polish commit.
