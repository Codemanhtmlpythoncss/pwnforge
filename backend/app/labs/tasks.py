"""Server-side grading and progress for guided lab worksheet tasks."""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Lab, LabInstance, LabTaskSubmission, User
from backend.app.security import crypto

_SERVICE_ALIASES = {
    "sshd": "ssh", "openssh": "ssh", "openssh-server": "ssh",
    "samba": "smbd", "smb": "smbd",
    "apache": "apache2", "httpd": "apache2",
    "node": "app-node", "nodejs": "app-node", "node.js": "app-node",
    "tomcat": "tomcat10", "postgres": "postgresql", "postmaster": "postgresql",
    "mysql": "mariadb",
}


def canonical_answer(value: str | list[str], kind: str) -> str:
    """Normalize authored and submitted values identically without leaking answers."""
    if kind in ("service_list", "list"):
        values = value if isinstance(value, list) else re.split(r"[,;\s]+", value)
        items = {str(part).strip().casefold().removesuffix(".service")
                 for part in values if str(part).strip()}
        if kind == "service_list":
            items = {_SERVICE_ALIASES.get(item, item) for item in items}
            items = {"php-fpm" if re.fullmatch(r"php\d+(?:\.\d+)?-fpm", item) else item
                     for item in items}
        return ",".join(sorted(items))
    return crypto.normalize_answer(str(value))


def public_tasks(session: Session, lab: Lab, user_id: int) -> list[dict]:
    tasks = list(lab.tasks or [])
    if not tasks:
        return []
    completed = set(session.execute(
        select(LabTaskSubmission.task_id).where(
            LabTaskSubmission.user_id == user_id,
            LabTaskSubmission.lab_id == lab.id,
        )
    ).scalars())
    return [{
        "id": task["id"],
        "prompt": task["prompt"],
        "kind": task.get("kind", "short_answer"),
        "hint": task.get("hint", ""),
        "explanation": task.get("explanation", "") if task["id"] in completed else "",
        "completed": task["id"] in completed,
        "points": task.get("points", 10),
    } for task in tasks]


def submit_task(session: Session, user: User, instance: LabInstance,
                task_id: str, answer: str) -> dict:
    lab = session.get(Lab, instance.lab_id)
    if lab is None:
        return {"correct": False, "message": "This lab definition is no longer available."}
    task = next((item for item in (lab.tasks or []) if item.get("id") == task_id), None)
    if task is None:
        return {"correct": False, "message": "Unknown lab task."}

    kind = task.get("kind", "short_answer")
    normalized = canonical_answer(answer, kind)
    submitted = crypto.hash_answer(normalized)
    expected_hashes = task.get("answer_hashes", [])
    if kind == "service_list":
        submitted_parts = {crypto.hash_answer(part) for part in normalized.split(",") if part}
        required = task.get("required_service_hashes", [])
        correct = bool(required) and all(
            any(crypto.constant_time_equals(expected, supplied) for supplied in submitted_parts)
            for expected in required
        )
    else:
        correct = any(crypto.constant_time_equals(submitted, expected)
                      for expected in expected_hashes)
    already_complete = session.execute(select(LabTaskSubmission.id).where(
        LabTaskSubmission.user_id == user.id,
        LabTaskSubmission.lab_id == lab.id,
        LabTaskSubmission.task_id == task_id,
    )).first() is not None
    if correct and not already_complete:
        session.add(LabTaskSubmission(user_id=user.id, lab_id=lab.id, task_id=task_id))
        session.flush()

    return {
        "task_id": task_id,
        "correct": correct,
        "completed": correct or already_complete,
        "already_complete": already_complete,
        "explanation": task.get("explanation", "") if correct else "",
        "hint": "" if correct else task.get("hint", ""),
    }


def all_tasks_complete(session: Session, lab: Lab, user_id: int) -> bool:
    tasks = list(lab.tasks or [])
    if not tasks:
        return True
    completed = set(session.execute(
        select(LabTaskSubmission.task_id).where(
            LabTaskSubmission.user_id == user_id,
            LabTaskSubmission.lab_id == lab.id,
        )
    ).scalars())
    return all(task["id"] in completed for task in tasks)
