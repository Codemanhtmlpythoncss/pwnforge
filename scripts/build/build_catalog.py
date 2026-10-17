#!/usr/bin/env python3
"""Materialise the authored catalogue into versioned YAML/JSON under catalog/.

This provides a reviewable, diffable export of the content (courses, profiles,
learning paths, labs, images, competencies, achievements) and supports bulk
export/import workflows. The authored Python modules remain the source of
truth; this script is a deterministic renderer.

Usage: python scripts/build/build_catalog.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from backend.app.catalog.content.achievements import ACHIEVEMENTS  # noqa: E402
from backend.app.catalog.content.competencies import COMPETENCIES  # noqa: E402
from backend.app.catalog.content.courses import ALL_COURSES  # noqa: E402
from backend.app.catalog.content.images import BASE_IMAGES  # noqa: E402
from backend.app.catalog.content.labs import LABS  # noqa: E402
from backend.app.catalog.content.paths import LEARNING_PATHS  # noqa: E402
from backend.app.catalog.content.profiles import generate_profiles  # noqa: E402

CATALOG = ROOT / "catalog"


def _dump_yaml(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))


def main() -> None:
    # Courses: one YAML per course for reviewable diffs.
    for c in ALL_COURSES:
        _dump_yaml(CATALOG / "courses" / f"{c['id']}.yaml", c)
    # Profiles: grouped by category to keep files manageable.
    profiles = generate_profiles()
    by_cat: dict[str, list] = {}
    for p in profiles:
        by_cat.setdefault(p["category"], []).append(p)
    for cat, items in by_cat.items():
        _dump_yaml(CATALOG / "profiles" / f"{cat}.yaml", items)
    _dump_yaml(CATALOG / "learning_paths" / "paths.yaml", LEARNING_PATHS)
    _dump_yaml(CATALOG / "components" / "labs.yaml", LABS)
    _dump_yaml(CATALOG / "components" / "images.yaml", BASE_IMAGES)
    _dump_yaml(CATALOG / "components" / "competencies.yaml",
               [{"domain": d, "key": k, "name": n, "description": desc}
                for (d, k, n, desc) in COMPETENCIES])
    _dump_yaml(CATALOG / "components" / "achievements.yaml", ACHIEVEMENTS)
    _write_schemas()
    print(f"Materialised: {len(ALL_COURSES)} courses, {len(profiles)} profiles, "
          f"{len(LEARNING_PATHS)} paths, {len(LABS)} labs, {len(BASE_IMAGES)} images, "
          f"{len(COMPETENCIES)} competencies -> {CATALOG}")


def _write_schemas() -> None:
    course_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["id", "title", "difficulty", "category", "lessons"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "difficulty": {"enum": ["orientation", "beginner", "easy", "intermediate",
                                     "hard", "advanced", "expert", "mastery"]},
            "category": {"type": "string"},
            "lessons": {"type": "array", "minItems": 1},
            "assessment": {"type": ["object", "null"]},
        },
    }
    profile_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["id", "name", "category", "difficulty", "os_family",
                     "vcpu", "memory_mb", "disk_gb"],
        "properties": {
            "id": {"type": "string"},
            "difficulty": {"enum": ["orientation", "beginner", "easy", "intermediate",
                                     "hard", "advanced", "expert", "mastery"]},
            "vcpu": {"type": "integer", "minimum": 1},
            "memory_mb": {"type": "integer", "minimum": 128},
            "disk_gb": {"type": "integer", "minimum": 1},
        },
    }
    (CATALOG / "schemas").mkdir(parents=True, exist_ok=True)
    (CATALOG / "schemas" / "course.schema.json").write_text(json.dumps(course_schema, indent=2))
    (CATALOG / "schemas" / "profile.schema.json").write_text(json.dumps(profile_schema, indent=2))


if __name__ == "__main__":
    main()
