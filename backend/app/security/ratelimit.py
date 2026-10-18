"""In-memory sliding-window rate limiter shared by the auth, public API and AI endpoints.

Per-process: with a single uvicorn worker (the default ``pwnforge serve``) that is
the whole server. Keys are opaque strings such as ``"auth:<ip>"`` or
``"api:token:<id>"`` and are never logged.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_HITS: dict[str, deque] = defaultdict(deque)
_LOCK = threading.Lock()


def hit(key: str, limit: int, window: int, now: float | None = None) -> int:
    """Record one request. Returns 0 when allowed, else seconds until the next slot frees."""
    now = time.time() if now is None else now
    with _LOCK:
        dq = _HITS[key]
        while dq and dq[0] <= now - window:
            dq.popleft()
        if len(dq) >= max(1, limit):
            return max(1, int(dq[0] + window - now) + 1)
        dq.append(now)
        return 0


def reset() -> None:
    """Forget everything (tests)."""
    with _LOCK:
        _HITS.clear()
