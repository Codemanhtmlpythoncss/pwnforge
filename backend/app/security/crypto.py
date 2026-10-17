"""Cryptographic helpers: password hashing, answer/flag hashing, token signing.

- Passwords use Argon2id (argon2-cffi).
- Assessment answers and flags are stored as salted SHA-256 hashes so the
  correct value never ships to the browser and server-side validation is the
  only way to pass. The salt is the process secret key.
- Sessions are signed with itsdangerous; the signed value carries only an
  opaque session id (looked up and revocable server-side).
"""
from __future__ import annotations

import hashlib
import hmac
import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from backend.app.core.config import get_settings

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError, Exception):
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _ph.check_needs_rehash(hashed)
    except Exception:
        return False


def normalize_answer(value: str) -> str:
    """Canonicalise a free-text answer before hashing/compare."""
    return re.sub(r"\s+", " ", value.strip().lower())


def hash_answer(value: str) -> str:
    """Salted hash for assessment answers / flags (not reversible)."""
    secret = get_settings().load_or_create_secret().encode()
    return hashlib.sha256(secret + b"::answer::" + normalize_answer(value).encode()).hexdigest()


def hash_flag(value: str) -> str:
    secret = get_settings().load_or_create_secret().encode()
    # Flags are case-sensitive except surrounding whitespace.
    return hashlib.sha256(secret + b"::flag::" + value.strip().encode()).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().load_or_create_secret(), salt="hacklab-session")


def sign_session(session_id: str) -> str:
    return _serializer().dumps({"sid": session_id})


def verify_session(token: str, max_age_seconds: int) -> str | None:
    try:
        data = _serializer().loads(token, max_age=max_age_seconds)
        return data.get("sid")
    except (BadSignature, SignatureExpired, Exception):
        return None
