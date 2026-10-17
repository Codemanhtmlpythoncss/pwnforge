# API

FastAPI serves interactive docs at **`/api/docs`** and the OpenAPI schema at
**`/api/openapi.json`**. All endpoints are under `/api`. Authentication is via
the session cookie (set by login) or a `Bearer` token. Responses are JSON.

## Auth
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/auth/status` | Whether initialised / registration open |
| POST | `/api/auth/bootstrap` | Create first admin (once) |
| POST | `/api/auth/login` | Sign in |
| POST | `/api/auth/register` | Self-service (if enabled) |
| POST | `/api/auth/logout` | Revoke session |
| GET | `/api/auth/me` | Current user |
| POST | `/api/auth/change-password` | Change own password |

## Learning
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/courses` | Search/filter/paginate |
| GET | `/api/courses/{id}` | Detail (answers hidden) |
| POST | `/api/courses/{id}/start` | Begin/resume |
| POST | `/api/lessons/{id}/complete` | Record completion |
| GET | `/api/lessons/{id}/hint?index=N` | Optional hint |
| GET | `/api/lessons/{id}/walkthrough` | Optional walkthrough |
| POST | `/api/exercises/{id}/submit` | Server-side graded |
| GET | `/api/exercises/{id}/hint?index=N` | Optional hint |
| POST | `/api/assessments/{id}/submit` | Server-side graded |
| GET | `/api/recommendations` | Next-step suggestions |
| GET | `/api/paths` / `/api/paths/{id}` | Learning paths |
| GET | `/api/competencies` / `/api/skills` | Competency map / dashboard |
| GET/POST/DELETE | `/api/bookmarks` | Bookmarks |

## Infrastructure
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/host/stats` / `/api/host/capabilities` | Real host metrics / driver |
| GET | `/api/profiles` / `/api/profiles/stats` / `/api/profiles/{id}` | Catalogue |
| GET/POST | `/api/vms` | List / create+start (returns `job_id`) |
| GET | `/api/vms/{id}` | VM detail (incl. `simulated`) |
| POST | `/api/vms/{id}/stop` `/reboot` `/reset` `/snapshot` | Lifecycle |
| DELETE | `/api/vms/{id}` | Delete |
| GET | `/api/labs` / `/api/labs/{id}` | Lab catalogue |
| GET/POST | `/api/lab-instances` | List / start (returns `job_id`) |
| POST/DELETE | `/api/lab-instances/{id}/stop`, `/api/lab-instances/{id}` | Stop / delete |
| POST | `/api/flags/submit` | Server-side flag validation |
| GET | `/api/images` (+ `/{key}/fetch` `/verify`, `/chain/validate`) | Admin |
| GET | `/api/networks` | Virtual networks |
| GET | `/api/storage/report`, POST `/api/storage/cleanup` | Storage |
| GET | `/api/jobs` / `/api/jobs/{id}` | Background job progress |

## Admin
| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/dashboard` | Dashboard aggregate |
| GET | `/api/achievements` | With earned status |
| GET | `/api/settings`, PUT `/api/settings/{key}` | Admin only |
| GET | `/api/settings/public` | UI-relevant settings |
| GET/POST/PUT | `/api/users` | Admin only |
| GET | `/api/audit` | Admin only |
| GET | `/api/admin/diagnostics`, POST `/api/admin/reconcile` | Admin only |

## WebSocket
| Path | Purpose |
|------|---------|
| `/api/ws/jobs/{job_id}` | Live job stage/percent stream |
| `/api/ws/terminal/{vm_id}` | Authorised guest terminal (xterm.js) |

### Example

```bash
curl -c jar -b jar -X POST localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' -d '{"username":"admin","password":"..."}'
curl -b jar 'localhost:8080/api/profiles?difficulty=hard&limit=5'
```
