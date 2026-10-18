"""The AI study assistant: a thin, careful client for an OpenAI-compatible chat API.

Configuration lives in the runtime settings (``ai.*``: base URL, model, timeouts, limits) and the API key, if the
provider needs one, in ``PWNFORGE_AI_API_KEY`` or ``<data_dir>/secrets/ai_api_key`` (0600). The key is only ever
sent from this server to the provider: no endpoint returns it, and it never reaches the browser.

Reliability:
  - a connection that can't be made (or a 502/503/504 before any answer) is retried twice, 1 s and 2 s apart;
    nothing is retried once the model has started answering, so nothing is ever said twice;
  - while the model reads the prompt, the stream to the browser gets a keep-alive every few seconds;
  - the wait for each piece of the answer is limited by ``ai.timeout_seconds``;
  - every failure becomes one error event with a type the page can act on (``unavailable``, ``timeout``,
    ``auth``, ``model``, ``rate_limited``, ``interrupted``, ``not_configured``, ``bad_response``) and never takes the
    server or the chat down.
"""
from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import os
import socket
import time
import urllib.parse
from collections.abc import AsyncIterator

import httpx
from sqlalchemy.orm import Session

from backend.app.core import settings_service as cfg
from backend.app.core.config import get_settings

log = logging.getLogger("pwnforge.ai")

SYSTEM_PROMPT = (
    "You are the study assistant of Pwnforge, a self-hosted cybersecurity training platform. The learner works on "
    "courses and on lab machines that run on their own Pwnforge host and that they are authorised to attack. "
    "Explain concepts clearly, step by step, at the learner's level; help them reason about what they observe; and "
    "always include how to detect or defend against a technique. Keep offensive guidance to the learner's Pwnforge "
    "lab machines, and decline requests aimed at systems the learner doesn't own or isn't authorised to test. "
    "Never invent flags or exercise answers: give hints that lead the learner to find them. If you are unsure, say so."
)
RETRY_DELAYS = (1.0, 2.0)
KEEPALIVE_SECONDS = 5.0


class AIError(Exception):
    def __init__(self, kind: str, message: str, status: int = 502, retryable: bool = False):
        super().__init__(message)
        self.kind, self.status, self.retryable = kind, status, retryable

    def event(self) -> dict:
        return {"type": "error", "kind": self.kind, "message": str(self), "retryable": self.retryable}


# ---- configuration ------------------------------------------------------------------------------
def key_file():
    return get_settings().data_dir / "secrets" / "ai_api_key"


def api_key() -> str:
    env = os.environ.get("PWNFORGE_AI_API_KEY", "").strip()
    if env:
        return env
    try:
        return key_file().read_text().strip()
    except OSError:
        return ""


def set_api_key(value: str) -> None:
    value = (value or "").strip()
    if not value or len(value) > 512 or any(c.isspace() for c in value):
        raise AIError("bad_request", "The API key looks wrong (no spaces, up to 512 characters).", 400)
    path = key_file()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, value.encode())
    finally:
        os.close(fd)
    os.replace(tmp, path)


def clear_api_key() -> None:
    try:
        key_file().unlink()
    except FileNotFoundError:
        pass


def is_local_host(host: str) -> bool:
    """True for this machine and private (LAN/VPN/tailnet) addresses."""
    host = (host or "").strip("[]").lower()
    if host in ("localhost", "") or host.endswith(".local") or host.endswith(".ts.net"):
        return True
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            ips = [ipaddress.ip_address(a[4][0]) for a in socket.getaddrinfo(host, None)[:4]]
        except OSError:
            return False
    return all(ip.is_private or ip.is_loopback or ip in ipaddress.ip_network("100.64.0.0/10") for ip in ips)


def validate_base_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise AIError("not_configured", "ai.base_url must be an http(s) URL such as http://127.0.0.1:11434/v1.", 503)
    if u.username or u.password or u.query or u.fragment:
        raise AIError("not_configured", "ai.base_url must not contain a user, password, query or fragment (put the key in the key setting).", 503)
    return url


def load(db: Session) -> dict:
    g = lambda k, d=None: cfg.get_setting(db, k, d)  # noqa: E731
    return {"enabled": bool(g("ai.enabled")), "base_url": (g("ai.base_url") or "").strip(), "model": (g("ai.model") or "").strip(),
            "allow_external": bool(g("ai.allow_external_provider")), "timeout": max(10, min(900, int(g("ai.timeout_seconds") or 120))),
            "max_tokens": max(16, min(16384, int(g("ai.max_tokens") or 1024))), "temperature": max(0.0, min(2.0, float(g("ai.temperature") or 0.3))),
            "rate": max(1, min(600, int(g("ai.rate_per_minute") or 20))), "system_prompt": (g("ai.system_prompt") or "").strip()[:4000]}


def check(conf: dict) -> str:
    """The validated base URL, or an AIError saying what to fix."""
    if not conf["enabled"]:
        raise AIError("not_configured", "The AI assistant is turned off. An administrator can turn it on in Settings (ai.enabled).", 503)
    if not conf["base_url"] or not conf["model"]:
        raise AIError("not_configured", "The AI assistant isn't set up yet: an administrator needs to set ai.base_url and ai.model.", 503)
    url = validate_base_url(conf["base_url"])
    host = urllib.parse.urlsplit(url).hostname or ""
    if not conf["allow_external"] and not is_local_host(host):
        raise AIError("not_configured", "ai.base_url points outside this host and its network. Allow it with ai.allow_external_provider "
                                        "(prompts would then leave your network).", 503)
    return url


def public_view(conf: dict) -> dict:
    host = ""
    try:
        host = urllib.parse.urlsplit(conf["base_url"]).hostname or ""
    except ValueError:
        pass
    return {"enabled": conf["enabled"], "configured": bool(conf["base_url"] and conf["model"]), "model": conf["model"],
            "provider_host": host, "local_provider": is_local_host(host) if host else None, "has_key": bool(api_key()),
            "timeout_seconds": conf["timeout"], "max_tokens": conf["max_tokens"], "rate_per_minute": conf["rate"]}


# ---- calling the model --------------------------------------------------------------------------
def _headers() -> dict:
    h = {"Content-Type": "application/json", "Accept": "text/event-stream", "User-Agent": "pwnforge-ai"}
    key = api_key()
    if key:
        h["Authorization"] = "Bearer " + key
    return h


def _http_error(status: int, body: bytes) -> AIError:
    detail = ""
    try:
        j = json.loads(body or b"{}")
        e = j.get("error")
        detail = (e.get("message") if isinstance(e, dict) else e) or j.get("detail") or ""
    except ValueError:
        pass
    detail = str(detail)[:200]
    if status in (401, 403):
        return AIError("auth", "The AI provider refused the API key. An administrator should check it.", 502)
    if status == 404:
        return AIError("model", "The provider doesn't know that model or address%s. Check ai.base_url and ai.model." % (": " + detail if detail else ""), 502)
    if status == 429:
        return AIError("rate_limited", "The AI provider is rate-limiting requests; try again in a minute.", 429, True)
    if status in (502, 503, 504):
        return AIError("unavailable", "The AI provider is unavailable (HTTP %d)%s." % (status, ": " + detail if detail else ""), 503, True)
    return AIError("bad_response", "The AI provider answered HTTP %d%s." % (status, ": " + detail if detail else ""), 502)


async def probe(conf: dict, transport: httpx.AsyncBaseTransport | None = None) -> dict:
    """Is the provider reachable, and does it list the model? (GET {base}/models, 5 s)"""
    try:
        url = check(conf)
    except AIError as e:
        return {"reachable": False, "error": str(e), "kind": e.kind}
    try:
        async with httpx.AsyncClient(timeout=5.0, transport=transport) as c:
            r = await c.get(url + "/models", headers=_headers())
        if r.status_code >= 400:
            e = _http_error(r.status_code, r.content)
            return {"reachable": r.status_code not in (502, 503, 504), "error": str(e), "kind": e.kind}
        ids = [m.get("id") for m in (r.json().get("data") or []) if isinstance(m, dict)]
        return {"reachable": True, "model_listed": conf["model"] in ids if ids else None, "models": ids[:50]}
    except (httpx.HTTPError, ValueError) as e:
        return {"reachable": False, "error": "Can't reach the AI provider: %s" % type(e).__name__, "kind": "unavailable"}


async def stream_chat(conf: dict, messages: list[dict], transport: httpx.AsyncBaseTransport | None = None) -> AsyncIterator[dict]:
    """Events: {"type": "delta", "text"} … then {"type": "done", "finish_reason"} or one {"type": "error", ...}."""
    url = check(conf) + "/chat/completions"
    payload = {"model": conf["model"], "messages": messages, "stream": True, "max_tokens": conf["max_tokens"],
               "temperature": conf["temperature"]}
    timeout = httpx.Timeout(connect=10.0, read=float(conf["timeout"]), write=30.0, pool=10.0)
    started = time.monotonic()
    attempt = 0
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        while True:
            try:
                async with client.stream("POST", url, json=payload, headers=_headers()) as r:
                    if r.status_code >= 400:
                        err = _http_error(r.status_code, await r.aread())
                        if err.kind == "unavailable" and attempt < len(RETRY_DELAYS):
                            raise _Retry(err)
                        yield err.event()
                        return
                    finished, got_any = None, False
                    async for line in r.aiter_lines():
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            finished = finished or "stop"
                            break
                        try:
                            j = json.loads(data)
                        except ValueError:
                            continue
                        if isinstance(j, dict) and j.get("error"):
                            e = j["error"]
                            yield AIError("bad_response", "The model reported an error: %s" % str(e.get("message") if isinstance(e, dict) else e)[:200]).event()
                            return
                        for ch in (j.get("choices") or [])[:1]:
                            text = (ch.get("delta") or {}).get("content") or ""
                            if text:
                                got_any = True
                                yield {"type": "delta", "text": text}
                            if ch.get("finish_reason"):
                                finished = ch["finish_reason"]
                    if finished is None:
                        yield AIError("interrupted", "The model's answer was cut off before it finished%s." % (
                            "" if got_any else " (nothing arrived)"), 502, True).event()
                        return
                    log.info("ai chat finished in %.1fs (%s)", time.monotonic() - started, finished)
                    yield {"type": "done", "finish_reason": finished}
                    return
            except _Retry as r:
                last = r.err
            except httpx.ReadTimeout:
                yield AIError("timeout", "The model didn't answer within %d s. It may still be loading; try again shortly." % conf["timeout"], 504, True).event()
                return
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last = AIError("unavailable", "Can't reach the AI provider (%s)." % type(e).__name__, 503, True)
            except httpx.HTTPError as e:   # dropped mid-answer: never retried (it would answer twice)
                log.warning("ai stream broke: %s", type(e).__name__)
                yield AIError("interrupted", "The connection to the AI provider dropped (%s)." % type(e).__name__, 502, True).event()
                return
            if attempt >= len(RETRY_DELAYS):
                log.warning("ai provider unreachable after %d tries: %s", attempt + 1, last)
                yield last.event()
                return
            await asyncio.sleep(RETRY_DELAYS[attempt])
            attempt += 1


class _Retry(Exception):
    def __init__(self, err: AIError):
        super().__init__(str(err))
        self.err = err


async def with_keepalive(events: AsyncIterator[dict], every: float = KEEPALIVE_SECONDS) -> AsyncIterator[dict | None]:
    """The events, with None every `every` seconds while nothing arrives (sent to the browser as a comment)."""
    queue: asyncio.Queue = asyncio.Queue()

    async def pump():
        try:
            async for ev in events:
                await queue.put(ev)
        except Exception as e:  # noqa: BLE001 -- one failed answer never takes the server down
            log.exception("ai stream failed")
            await queue.put(AIError("bad_response", "The assistant hit an error: %s" % type(e).__name__).event())
        finally:
            await queue.put(_END)
    task = asyncio.create_task(pump())
    try:
        while True:
            try:
                ev = await asyncio.wait_for(queue.get(), timeout=every)
            except asyncio.TimeoutError:
                yield None
                continue
            if ev is _END:
                return
            yield ev
    finally:
        task.cancel()


_END = object()


def build_messages(conf: dict, history: list[dict], context: str = "") -> list[dict]:
    system = SYSTEM_PROMPT + ("\n\n" + conf["system_prompt"] if conf["system_prompt"] else "") + ("\n\n" + context if context else "")
    return [{"role": "system", "content": system}] + history


def lesson_context(db: Session, course_id: str | None, lesson_id: str | None) -> str:
    """The course or lesson the learner is on (title and the start of its text; never answers)."""
    from backend.app.database.models import Course, Lesson
    if lesson_id:
        lesson = db.get(Lesson, lesson_id)
        if lesson is not None:
            return "The learner is on the lesson \"%s\":\n%s" % (lesson.title, (lesson.body or "")[:2000])
    if course_id:
        course = db.get(Course, course_id)
        if course is not None:
            return "The learner is on the course \"%s\": %s" % (course.title, (course.description or "")[:1000])
    return ""
