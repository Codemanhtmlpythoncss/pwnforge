"""Catalogue integrity: real counts, search, validation, graph integrity."""
from __future__ import annotations

from backend.app.catalog.content.courses import ALL_COURSES, validate_unique_ids
from backend.app.catalog.content.profiles import generate_profiles, MIN_PROFILES


def test_at_least_50_courses():
    assert len(ALL_COURSES) >= 50
    validate_unique_ids()


def test_at_least_1000_profiles():
    profs = generate_profiles()
    assert len(profs) >= MIN_PROFILES
    ids = [p["id"] for p in profs]
    assert len(set(ids)) == len(ids), "profile ids must be unique"


def test_profiles_cover_all_difficulties():
    diffs = {p["difficulty"] for p in generate_profiles()}
    for d in ("easy", "intermediate", "hard", "advanced", "expert"):
        assert d in diffs


def test_catalogue_counts_via_api(admin):
    assert admin.get("/api/courses?limit=1").json()["total"] >= 50
    assert admin.get("/api/profiles/stats").json()["total"] >= 1000


def test_profile_search(admin):
    r = admin.get("/api/profiles?q=sqli&limit=10").json()
    assert r["total"] > 0
    assert all("sqli" in p["id"] or "sqli" in p["name"].lower() for p in r["items"])


def test_profile_filter_by_difficulty_and_os(admin):
    r = admin.get("/api/profiles?difficulty=hard&os_family=debian&limit=20").json()
    assert all(p["difficulty"] == "hard" and p["os_family"] == "debian" for p in r["items"])


def test_pagination(admin):
    p1 = admin.get("/api/profiles?limit=10&offset=0").json()["items"]
    p2 = admin.get("/api/profiles?limit=10&offset=10").json()["items"]
    assert {p["id"] for p in p1}.isdisjoint({p["id"] for p in p2})


def test_lab_machine_refs_exist(admin):
    # Every lab machine references a real profile.
    labs = admin.get("/api/labs").json()["items"]
    assert len(labs) >= 5
    for lab in labs:
        detail = admin.get(f"/api/labs/{lab['id']}").json()
        for m in detail["machines"]:
            prof = admin.get(f"/api/profiles/{m['profile_id']}")
            assert prof.status_code == 200, f"{lab['id']} -> missing {m['profile_id']}"


def test_learning_paths_reference_real_courses(admin):
    paths = admin.get("/api/paths").json()["items"]
    assert len(paths) >= 8
    for p in paths:
        d = admin.get(f"/api/paths/{p['id']}").json()
        for step in d["steps"]:
            assert step["title"]  # resolved title


def test_every_course_has_lessons_and_assessment():
    for c in ALL_COURSES:
        assert len(c["lessons"]) >= 1, f"{c['id']} has no lessons"
        assert c["assessment"] is not None, f"{c['id']} has no assessment"
        assert c["objectives"], f"{c['id']} has no objectives"
