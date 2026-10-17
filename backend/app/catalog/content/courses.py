"""Aggregated course catalogue."""
from __future__ import annotations

from backend.app.catalog.content import (
    courses_defensive, courses_foundations, courses_methodology, courses_osint,
    courses_specialist, courses_systems, courses_web,
)

ALL_COURSES: list[dict] = (
    courses_foundations.COURSES
    + courses_systems.COURSES
    + courses_web.COURSES
    + courses_methodology.COURSES
    + courses_defensive.COURSES
    + courses_specialist.COURSES
    + courses_osint.COURSES
)


def validate_unique_ids() -> None:
    ids = [c["id"] for c in ALL_COURSES]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"Duplicate course ids: {sorted(dupes)}")
