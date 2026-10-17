"""Pydantic request/response schemas for the API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class BootstrapRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    display_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    email: str | None = None
    display_name: str | None = None


class CreateUserRequest(BaseModel):
    username: str
    password: str = Field(min_length=8)
    role: str = "learner"
    email: str | None = None
    display_name: str | None = None


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    display_name: str | None = None
    preferred_specialization: str | None = None


class CompleteLessonRequest(BaseModel):
    hints_used: int = 0
    walkthrough_opened: bool = False


class SubmitExerciseRequest(BaseModel):
    answer: str


class SubmitAssessmentRequest(BaseModel):
    answers: dict[str, str]


class SubmitFlagRequest(BaseModel):
    scope_type: str
    scope_id: str
    value: str


class StartVMRequest(BaseModel):
    profile_id: str
    name: str | None = None
    persistent: bool = False


class SnapshotRequest(BaseModel):
    name: str
    kind: str = "disk"


class StartLabRequest(BaseModel):
    lab_id: str


class SettingUpdate(BaseModel):
    value: object


class BookmarkRequest(BaseModel):
    kind: str
    ref_id: str
