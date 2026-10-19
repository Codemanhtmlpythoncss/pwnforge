"""Pwnforge FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.app.api import (
    routes_admin, routes_ai, routes_auth, routes_infra, routes_learning, routes_remote, routes_tokens, routes_v1, routes_ws,
)
from backend.app.core.config import get_settings
from backend.app.database.base import session_scope
from backend.app.jobs import handlers  # noqa: F401 - registers job handlers
from backend.app.security import ratelimit

_AUTH_MAX, _AUTH_WINDOW = 20, 60   # sign-in attempts per IP per minute

API_DESCRIPTION = """
The Pwnforge API. **Start with the public API (`/api/v1`)**: status, courses, labs, your VMs and lab instances,
and starting or stopping your labs. The AI assistant is under `/api/ai`.

**Authentication.** Create a personal API token in the website (Developer › API tokens) and send it as
`Authorization: Bearer pf_...`. Tokens have scopes (`read`, `labs`, `ai`), never exceed your role, work only with
`/api/v1` and `/api/ai`, and can be revoked at any time. Use **Authorize** above to try requests here.

**Errors** are JSON: `{"detail": "..."}` with the usual status codes (401 not signed in, 403 not allowed,
404 not found or not yours, 409 conflict, 422 invalid input, 429 rate-limited with `Retry-After`).

Guides: `docs/API.md`, `docs/AI_API.md` and `docs/REMOTE_ACCESS.md` in the repository, and the Developer page.
"""
TAGS = [
    {"name": "public API v1", "description": "Stable endpoints for scripts and tools (token or session)."},
    {"name": "AI assistant", "description": "The study assistant (token with the `ai` scope, or session)."},
    {"name": "API tokens", "description": "Create and revoke personal API tokens (signed-in session only)."},
    {"name": "remote access", "description": "Reaching lab machines privately: jump host, OpenVPN, Tailscale."},
    {"name": "auth", "description": "Website sign-in (cookie sessions)."},
    {"name": "learning", "description": "The website's course and progress endpoints."},
    {"name": "infra", "description": "The website's machine, lab and storage endpoints."},
    {"name": "admin", "description": "Administration (administrators only)."},
]

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Pwnforge", version="1.0.0", description=API_DESCRIPTION, openapi_tags=TAGS,
                  docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")

    # CORS: localhost always; LAN origins from settings.
    origins = {"http://localhost:5173", "http://127.0.0.1:5173",
               f"http://localhost:{settings.port}", f"http://127.0.0.1:{settings.port}"}
    try:
        with session_scope() as db:
            from backend.app.core import settings_service as cfg
            for o in (cfg.get_setting(db, "server.allowed_origins") or []):
                origins.add(o)
    except Exception:
        pass
    app.add_middleware(
        CORSMiddleware, allow_origins=list(origins), allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_and_rate(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/auth/") and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            wait = ratelimit.hit("auth:" + ip, _AUTH_MAX, _AUTH_WINDOW)
            if wait:
                return JSONResponse({"detail": "Too many requests, slow down."},
                                    status_code=429, headers={"Retry-After": str(wait)})
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "0"
        # CSP suited to a self-hosted SPA (no third-party origins).
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'; "
            "connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'")
        return response

    # Routers
    app.include_router(routes_auth.router)
    app.include_router(routes_learning.router)
    app.include_router(routes_infra.router)
    app.include_router(routes_admin.router)
    app.include_router(routes_ws.router)
    app.include_router(routes_v1.router)
    app.include_router(routes_tokens.router)
    app.include_router(routes_ai.router)
    app.include_router(routes_remote.router)
    _openapi_security(app)
    _api_docs(app)

    @app.on_event("startup")
    def _refresh_readiness() -> None:
        if settings.environment.lower() == "test":
            return   # tests seed readiness themselves; don't race the test DB
        # Profile readiness depends on the host's VM capabilities, which change when real machines are
        # set up. Recompute it on startup (in the background, best-effort) so a restart after setup flips
        # profiles to 'ready' without a reseed. recompute_readiness only writes rows that actually change.
        import threading

        def run() -> None:
            try:
                from backend.app.database.base import session_scope
                from backend.app.profiles import service as profiles
                with session_scope() as db:
                    profiles.recompute_readiness(db)
            except Exception:  # noqa: BLE001 - never block or crash startup
                pass
        threading.Thread(target=run, name="readiness-refresh", daemon=True).start()

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": app.version}

    _mount_frontend(app)
    return app


def _openapi_security(app: FastAPI) -> None:
    """Bearer tokens (and the website's cookie) in the OpenAPI document, so Swagger's Authorize button works."""
    def schema():
        if app.openapi_schema:
            return app.openapi_schema
        s = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes, tags=app.openapi_tags)
        s.setdefault("components", {})["securitySchemes"] = {
            "bearerAuth": {"type": "http", "scheme": "bearer", "description": "A personal API token: pf_..."},
            "cookieAuth": {"type": "apiKey", "in": "cookie", "name": "pwnforge_session", "description": "The website's session"},
        }
        for path, ops in s.get("paths", {}).items():
            if path.startswith(("/api/v1/", "/api/ai/", "/api/tokens", "/api/remote", "/api/vpn")):
                for op in ops.values():
                    if isinstance(op, dict):
                        op["security"] = [{"bearerAuth": []}, {"cookieAuth": []}] if path.startswith(("/api/v1/", "/api/ai/")) else [{"cookieAuth": []}]
        app.openapi_schema = s
        return s
    app.openapi = schema


SWAGGER_DIR = "swagger"     # frontend/dist/swagger: Swagger UI's files, copied there by the frontend build


def _api_docs(app: FastAPI) -> None:
    """Interactive API docs served entirely from this server (the strict CSP allows no CDN or inline scripts)."""
    @app.get("/api/docs", include_in_schema=False)
    def docs() -> HTMLResponse:
        assets = get_settings().repo_root / "frontend" / "dist" / SWAGGER_DIR / "swagger-ui-bundle.js"
        if not assets.exists():
            return HTMLResponse("<!doctype html><title>Pwnforge API</title><body style='font-family:sans-serif;max-width:40em;margin:3em auto'>"
                                "<h1>Pwnforge API</h1><p>The interactive docs need the website built "
                                "(<code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>). The OpenAPI document is at "
                                "<a href='/api/openapi.json'>/api/openapi.json</a>; the guides are docs/API.md and docs/AI_API.md.</p>")
        return HTMLResponse(
            "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>Pwnforge API</title><link rel='stylesheet' href='/swagger/swagger-ui.css'></head>"
            "<body><div id='swagger-ui'></div><script src='/swagger/swagger-ui-bundle.js'></script>"
            "<script src='/api/docs/init.js'></script></body></html>")

    @app.get("/api/docs/init.js", include_in_schema=False)
    def docs_init() -> Response:
        js = ("window.ui = SwaggerUIBundle({url: '/api/openapi.json', dom_id: '#swagger-ui', deepLinking: true,"
              " persistAuthorization: false, tryItOutEnabled: false, docExpansion: 'list', defaultModelsExpandDepth: 0});")
        return Response(js, media_type="application/javascript")


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built SPA if present; otherwise a helpful placeholder."""
    dist = get_settings().repo_root / "frontend" / "dist"
    index = dist / "index.html"
    if index.exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str):
            # Never let the SPA catch-all swallow the API.
            if full_path.startswith("api/"):
                return JSONResponse({"detail": "Not found"}, status_code=404)
            candidate = dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(index))
    else:
        @app.get("/")
        def placeholder():
            return JSONResponse({
                "message": "Pwnforge backend is running. Build the frontend "
                           "(cd frontend && npm install && npm run build) to serve the UI.",
                "api_docs": "/api/docs", "health": "/api/health"})


app = create_app()
