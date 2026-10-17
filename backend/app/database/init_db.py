"""Schema creation and seeding.

Production deployments apply Alembic migrations (``backend/migrations``). For
tests and first-run bootstrap, ``create_schema`` builds the schema directly
from the ORM metadata. ``seed`` is idempotent and safe to re-run.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.catalog import importer
from backend.app.core import settings_service
from backend.app.database.base import Base, get_engine, session_scope
from backend.app.profiles import service as profiles_service


def create_schema() -> None:
    Base.metadata.create_all(bind=get_engine())


def seed(*, include_profiles: bool = True, recompute_readiness: bool = True) -> dict:
    with session_scope() as session:
        settings_service.ensure_defaults(session)
        counts = importer.import_all(session, include_profiles=include_profiles)
    if recompute_readiness and include_profiles:
        with session_scope() as session:
            counts["readiness"] = profiles_service.recompute_readiness(session)
    return counts


def initialise(*, include_profiles: bool = True) -> dict:
    create_schema()
    return seed(include_profiles=include_profiles)
