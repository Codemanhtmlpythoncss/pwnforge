"""The AI study assistant's API (/api/ai). Documented in docs/AI_API.md.

  GET    /api/ai/status     is it on, which model, is the provider reachable (never the key)
  POST   /api/ai/chat       a conversation turn; streams server-sent events (or JSON with "stream": false)
  PUT    /api/ai/key        administrators: set the provider's API key (stored server-side, 0600)
  DELETE /api/ai/key        administrators: remove it

Works with a signed-in session or an API token with the ``ai`` scope.
"""
from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.app.ai import service as ai
from backend.app.api.deps import client_ip, get_db, require_admin, require_scope, session_only
from backend.app.database.base import session_scope
from backend.app.database.models import User
from backend.app.security import audit, ratelimit

router = APIRouter(prefix="/api/ai", tags=["AI assistant"])
_PROBE: dict = {"at": 0.0, "key": None, "data": None}


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user"])
    content: str = Field(..., min_length=1, max_length=8000)

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role must be user or assistant")
        return v


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=40)
    course_id: str | None = Field(None, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    lesson_id: str | None = Field(None, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
    stream: bool = True


class KeyRequest(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=512)


@router.get("/status", summary="Is the assistant on, which model, is the provider reachable")
async def status(request: Request, user: User = Depends(require_scope("ai")), db: Session = Depends(get_db)) -> dict:
    conf = ai.load(db)
    out = ai.public_view(conf)
    key = (conf["base_url"], conf["model"], conf["enabled"], conf["allow_external"])
    if time.time() - _PROBE["at"] > 30 or _PROBE["key"] != key:
        _PROBE.update(at=time.time(), key=key, data=await ai.probe(conf))
    out["provider"] = _PROBE["data"]
    return out


@router.post("/chat", summary="Ask the assistant (server-sent events)")
async def chat(body: ChatRequest, request: Request, user: User = Depends(require_scope("ai")), db: Session = Depends(get_db)):
    conf = ai.load(db)
    row = getattr(request.state, "api_token", None)
    who = ("token:" + row.id) if row is not None else ("user:%d" % user.id)
    wait = ratelimit.hit("ai:" + who, conf["rate"], 60)
    if wait:
        raise HTTPException(429, "Too many questions in a minute; try again in %d s." % wait, headers={"Retry-After": str(wait)})
    try:
        ai.check(conf)
    except ai.AIError as e:
        return JSONResponse({"detail": str(e), "kind": e.kind}, status_code=e.status)
    if body.messages[-1].role != "user":
        raise HTTPException(422, "The last message must be the user's question.")
    messages = ai.build_messages(conf, [m.model_dump() for m in body.messages], ai.lesson_context(db, body.course_id, body.lesson_id))
    user_id, ip, n = user.id, client_ip(request), len(body.messages)
    audit.record(db, action="ai.chat", actor_id=user_id, detail={"model": conf["model"], "messages": n,
                 "via": "token" if row is not None else "session"}, ip=ip)
    db.commit()
    events = ai.stream_chat(conf, messages, transport=getattr(request.app.state, "ai_transport", None))

    if not body.stream:
        text, last = [], None
        async for ev in events:
            if ev["type"] == "delta":
                text.append(ev["text"])
            last = ev
        if last and last["type"] == "error":
            return JSONResponse({"detail": last["message"], "kind": last["kind"], "retryable": last["retryable"], "partial": "".join(text)},
                                status_code=503 if last["kind"] in ("unavailable", "not_configured") else 504 if last["kind"] == "timeout" else 502)
        return {"reply": "".join(text), "finish_reason": (last or {}).get("finish_reason")}

    async def sse():
        yield b": connected\n\n"
        outcome = "done"
        try:
            async for ev in ai.with_keepalive(events):
                if await request.is_disconnected():
                    outcome = "client_gone"
                    return
                if ev is None:
                    yield b": keep-alive\n\n"
                    continue
                if ev["type"] == "error":
                    outcome = ev["kind"]
                yield ("data: %s\n\n" % json.dumps(ev)).encode()
        finally:
            if outcome != "done":
                try:
                    with session_scope() as s:
                        audit.record(s, action="ai.chat.failed", actor_id=user_id, detail={"kind": outcome}, ip=ip)
                except Exception:  # noqa: BLE001 -- the audit row is best effort here
                    pass
    return StreamingResponse(sse(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@router.put("/key", summary="Administrators: set the AI provider's API key")
def set_key(body: KeyRequest, request: Request, user: User = Depends(require_admin), _s: User = Depends(session_only),
            db: Session = Depends(get_db)) -> dict:
    try:
        ai.set_api_key(body.api_key)
    except ai.AIError as e:
        raise HTTPException(e.status, str(e))
    audit.record(db, action="ai.key.set", actor_id=user.id, ip=client_ip(request))
    _PROBE["at"] = 0
    return {"ok": True, "has_key": True}


@router.delete("/key", summary="Administrators: remove the AI provider's API key")
def clear_key(request: Request, user: User = Depends(require_admin), _s: User = Depends(session_only), db: Session = Depends(get_db)) -> dict:
    ai.clear_api_key()
    audit.record(db, action="ai.key.clear", actor_id=user.id, ip=client_ip(request))
    _PROBE["at"] = 0
    return {"ok": True, "has_key": bool(ai.api_key())}

