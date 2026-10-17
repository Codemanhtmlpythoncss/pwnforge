"""Background job runner.

Long-running operations (VM start, lab start, image fetch) run on a thread
pool and report progress into the ``jobs`` table so the API/WebSocket layer can
stream real progress. Each job opens its own DB session. A per-target lock
prevents concurrent conflicting operations on the same VM/lab.
"""
from __future__ import annotations

import threading
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from backend.app.database.base import get_session_factory, session_scope
from backend.app.database.models import Job, JobStatus

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="hacklab-job")
_target_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_locks_guard = threading.Lock()

# Registry of job kind -> callable(session, job, params, progress)
_registry: dict[str, Callable] = {}


def register(kind: str):
    def deco(fn: Callable):
        _registry[kind] = fn
        return fn
    return deco


def target_lock(key: str) -> threading.Lock:
    with _locks_guard:
        return _target_locks[key]


class JobProgress:
    """Progress reporter handed to job bodies.

    Writes stage/percent/steps through the *same* session the handler uses and
    commits, so (a) there is never a competing writer on SQLite's single-writer
    lock, and (b) progress becomes visible to pollers immediately. The handler
    keeps using the session after the commit (expire_on_commit is False).
    """

    def __init__(self, session, job: Job) -> None:
        self.session = session
        self.job = job

    def update(self, percent: int | None = None, stage: str | None = None,
               step_status: str = "running", detail: str = "") -> None:
        if percent is not None:
            self.job.progress = max(0, min(100, percent))
        if stage is not None:
            self.job.stage = stage
            steps = list(self.job.steps or [])
            steps.append({
                "stage": stage, "status": step_status,
                "ts": datetime.now(timezone.utc).isoformat(), "detail": detail,
            })
            self.job.steps = steps
        # Commit flushes the handler's pending work too, releasing the write
        # lock and publishing progress to other connections.
        self.session.commit()


def enqueue(kind: str, *, params: dict, owner_id: int | None = None,
            target_type: str | None = None, target_id: str | None = None,
            lock_key: str | None = None) -> str:
    """Create a job row and schedule it. Returns the job id."""
    if kind not in _registry:
        raise KeyError(f"No job handler registered for '{kind}'")
    with session_scope() as session:
        job = Job(kind=kind, owner_id=owner_id, target_type=target_type,
                  target_id=target_id, status=JobStatus.queued)
        session.add(job)
        session.flush()
        job_id = job.id
    _executor.submit(_run, kind, job_id, params, lock_key or target_id or job_id)
    return job_id


def run_sync(kind: str, *, params: dict, owner_id: int | None = None,
             target_type: str | None = None, target_id: str | None = None) -> str:
    """Run a job synchronously (used by the CLI and tests). Returns job id."""
    with session_scope() as session:
        job = Job(kind=kind, owner_id=owner_id, target_type=target_type,
                  target_id=target_id, status=JobStatus.queued)
        session.add(job)
        session.flush()
        job_id = job.id
    _run(kind, job_id, params, target_id or job_id)
    return job_id


def _run(kind: str, job_id: str, params: dict, lock_key: str) -> None:
    handler = _registry[kind]
    lock = target_lock(lock_key)
    with lock:
        session = get_session_factory()()
        try:
            job = session.get(Job, job_id)
            job.status = JobStatus.running
            job.started_at = datetime.now(timezone.utc)
            session.commit()
            progress = JobProgress(session, job)
            result = handler(session, job, params, progress)
            job.status = JobStatus.succeeded
            job.progress = 100
            job.finished_at = datetime.now(timezone.utc)
            if isinstance(result, dict):
                job.result = result
            session.commit()
        except Exception as exc:  # noqa: BLE001
            # Persist whatever terminal state the handler set (e.g. instance
            # status=error) when the session is still valid; otherwise roll back.
            try:
                session.commit()
            except Exception:
                session.rollback()
            job = session.get(Job, job_id)
            if job is not None:
                job.status = JobStatus.failed
                job.error = f"{type(exc).__name__}: {exc}"
                job.finished_at = datetime.now(timezone.utc)
                steps = list(job.steps or [])
                steps.append({"stage": "error", "status": "failed",
                              "ts": datetime.now(timezone.utc).isoformat(),
                              "detail": "".join(
                                  traceback.format_exception_only(type(exc), exc)).strip()})
                job.steps = steps
                session.commit()
        finally:
            session.close()


def shutdown() -> None:  # pragma: no cover
    _executor.shutdown(wait=False, cancel_futures=True)
