"""Pwnforge FastAPI application factory."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import (
    routes_admin, routes_auth, routes_infra, routes_learning, routes_ws,
)
from backend.app.core.config import get_settings
from backend.app.database.base import session_scope
from backend.app.jobs import handlers  # noqa: F401 - registers job handlers

# Simple in-memory rate limiter for auth endpoints (per-IP).
_RATE: dict[str, deque] = defaultdict(deque)
_RATE_WINDOW = 60
_RATE_MAX = 20  # auth attempts per window per IP


def _rate_limited(ip: str) -> bool:
    now = time.time()
    dq = _RATE[ip]
    while dq and dq[0] < now - _RATE_WINDOW:
        dq.popleft()
    if len(dq) >= _RATE_MAX:
        return True
    dq.append(now)
    return False


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Pwnforge", version="1.0.0",
                  description="Self-hosted cybersecurity training platform",
                  docs_url="/api/docs", openapi_url="/api/openapi.json")

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
            if _rate_limited(ip):
                return JSONResponse({"detail": "Too many requests, slow down."},
                                    status_code=429)
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

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "version": app.version}

    _mount_frontend(app)
    return app


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
