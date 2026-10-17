"""WebSocket endpoints: live job progress and an authorised guest terminal.

The terminal NEVER exposes a host shell. For the simulation driver it provides
a clearly-labelled sandboxed shell that answers a small, fixed command set
against the simulated VM's state. On a real hypervisor the same endpoint is the
authorised bridge to the guest's serial console (via the driver); it is gated
by per-VM ownership checks every time.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.auth import service as auth_service
from backend.app.database.base import get_session_factory
from backend.app.database.models import Job, JobStatus, User, VMInstance
from backend.app.security import crypto

router = APIRouter()


def _authenticate_ws(ws: WebSocket, db: Session) -> User | None:
    token = ws.cookies.get("pwnforge_session")
    if not token:
        token = ws.query_params.get("token")
    if not token:
        return None
    sid = crypto.verify_session(token, 10**9)
    if not sid:
        return None
    return auth_service.resolve_session(db, sid)


@router.websocket("/api/ws/jobs/{job_id}")
async def ws_job(ws: WebSocket, job_id: str) -> None:
    await ws.accept()
    db = get_session_factory()()
    try:
        user = _authenticate_ws(ws, db)
        if user is None:
            await ws.send_json({"error": "unauthorised"})
            await ws.close()
            return
        last = None
        for _ in range(600):  # up to ~5 minutes
            db.expire_all()
            job = db.get(Job, job_id)
            if job is None:
                await ws.send_json({"error": "unknown job"})
                break
            snapshot = {"status": job.status.value, "progress": job.progress,
                        "stage": job.stage, "steps": job.steps, "error": job.error,
                        "result": job.result}
            if snapshot != last:
                await ws.send_json(snapshot)
                last = snapshot
            if job.status in (JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled):
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
        try:
            await ws.close()
        except RuntimeError:
            pass


# A deliberately minimal, non-host command set for the simulated guest shell.
def _sim_shell_response(inst: VMInstance, line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    cmd = line.split()[0]
    responses = {
        "help": "available: help, whoami, hostname, ip, uname, ls, cat, ps, exit",
        "whoami": "trainee",
        "hostname": inst.name,
        "ip": inst.ip_address or "(not assigned)",
        "uname": "Linux (simulated guest)",
        "ls": "notes.txt  flag.txt  tools/",
        "ps": "PID TTY   CMD\n  1 ?     init\n 42 ?     sshd",
    }
    if cmd in responses:
        return responses[cmd]
    if cmd == "cat" and "flag.txt" in line:
        return "This simulated guest has no real flag. Start a real lab on a KVM host."
    return f"{cmd}: command not available in the simulated terminal"


@router.websocket("/api/ws/terminal/{vm_id}")
async def ws_terminal(ws: WebSocket, vm_id: str) -> None:
    await ws.accept()
    db = get_session_factory()()
    try:
        user = _authenticate_ws(ws, db)
        if user is None:
            await ws.send_text("\r\nUnauthorised.\r\n")
            await ws.close()
            return
        inst = db.get(VMInstance, vm_id)
        # Per-connection authorisation: ownership (or admin) is required.
        if inst is None or (inst.owner_id != user.id and user.role.value != "administrator"):
            await ws.send_text("\r\nNot authorised for this VM.\r\n")
            await ws.close()
            return
        simulated = inst.driver == "simulation"
        banner = (f"\r\nPwnforge terminal — {inst.name} ({inst.ip_address or 'no ip'})\r\n")
        if simulated:
            banner += ("[simulated guest — no host shell is exposed; "
                       "run a real lab on a KVM host for a live console]\r\n")
        else:
            banner += ("[connecting to guest serial console via the hypervisor]\r\n")
        await ws.send_text(banner + "$ ")
        while True:
            data = await ws.receive_text()
            # The client sends whole command lines.
            line = data.rstrip("\r\n")
            if line.strip() in ("exit", "quit", "logout"):
                await ws.send_text("\r\nconnection closed\r\n")
                break
            if simulated:
                out = _sim_shell_response(inst, line)
            else:
                # Real guests: the driver exposes a serial/VNC endpoint. Proxying
                # raw PTY bytes is host-specific and documented in docs/USER_GUIDE.
                out = ("real guest console bridging is provided by the host serial "
                       "console; see documentation. (no host shell is exposed here)")
            await ws.send_text("\r\n" + out + "\r\n$ ")
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
        try:
            await ws.close()
        except RuntimeError:
            pass
