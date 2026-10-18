"""Personal API tokens (Developer › API tokens). Managing tokens needs a signed-in session: a token can't make,
list or revoke tokens. The full token is returned once, when it is created; afterwards only its last characters.

  GET    /api/tokens               your tokens (administrators: everyone's with all=true)
  GET    /api/tokens/scopes        the scopes your role can grant
  POST   /api/tokens               {"name", "scopes": ["read", "labs", "ai"], "expires_days": 90}
  DELETE /api/tokens/{id}          revoke one (yours; administrators: anyone's)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import client_ip, get_db, session_only
from backend.app.auth import tokens
from backend.app.database.models import User, UserRole
from backend.app.security import audit

router = APIRouter(prefix="/api/tokens", tags=["API tokens"])


class NewToken(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, examples=["lab-automation"])
    scopes: list[str] = Field(..., min_length=1, max_length=3, examples=[["read", "labs"]])
    expires_days: int | None = Field(90, ge=1, le=tokens.MAX_DAYS)


@router.get("", summary="Your API tokens")
def listing(all: bool = False, user: User = Depends(session_only), db: Session = Depends(get_db)) -> dict:
    return {"items": tokens.listing(db, user, everyone=all and user.role == UserRole.administrator)}


@router.get("/scopes", summary="Scopes your role can grant")
def scopes(user: User = Depends(session_only)) -> dict:
    allowed = tokens.allowed_scopes(user)
    return {"items": [{"scope": k, "description": v, "allowed": k in allowed} for k, v in tokens.SCOPES.items()]}


@router.post("", status_code=201, summary="Create a token (shown once)")
def create(body: NewToken, request: Request, user: User = Depends(session_only), db: Session = Depends(get_db)) -> dict:
    try:
        row, secret = tokens.create(db, user, name=body.name, scopes=body.scopes, expires_days=body.expires_days)
    except tokens.TokenError as e:
        raise HTTPException(400, str(e))
    audit.record(db, action="token.create", actor_id=user.id, target_type="api_token", target_id=row.id,
                 detail={"name": row.name, "scopes": row.scopes}, ip=client_ip(request))
    return dict(tokens.public(row), token=secret,
                warning="Copy this token now: it is shown only once. Treat it like a password.")


@router.delete("/{token_id}", summary="Revoke a token")
def revoke(request: Request, token_id: str = Path(..., pattern=r"^[0-9a-f]{32}$"), user: User = Depends(session_only),
           db: Session = Depends(get_db)) -> dict:
    try:
        row = tokens.revoke(db, token_id, user)
    except tokens.TokenError:
        raise HTTPException(404, "No such token.")
    audit.record(db, action="token.revoke", actor_id=user.id, target_type="api_token", target_id=row.id, ip=client_ip(request))
    return tokens.public(row)
