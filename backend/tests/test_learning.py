"""Course progress, difficulty, prerequisites, competencies, assessments."""
from __future__ import annotations


def _answer_assessment(client, detail):
    """Build correct answers from the authored content (via the DB hashes)."""
    # We cannot read correct answers from the API (by design). Instead, drive
    # the known-correct answers for a specific course.
    pass


def test_course_detail_hides_answers(admin):
    d = admin.get("/api/courses/cybersecurity-fundamentals").json()
    for a in d["assessments"]:
        for q in a["questions"]:
            assert "answer" not in q and "answer_hash" not in q


def test_start_and_complete_lessons_updates_progress(admin):
    cid = "linux-fundamentals"
    d = admin.get(f"/api/courses/{cid}").json()
    admin.post(f"/api/courses/{cid}/start")
    for l in d["lessons"]:
        r = admin.post(f"/api/lessons/{l['id']}/complete",
                       json={"hints_used": 0, "walkthrough_opened": False})
        assert r.status_code == 200
    prog = admin.get(f"/api/courses/{cid}").json()["progress"]
    assert prog["percent"] == 100.0


def test_assessment_correct_vs_incorrect(admin):
    # Fundamentals assessment: we know the correct answers from the content.
    cid = "cybersecurity-fundamentals"
    d = admin.get(f"/api/courses/{cid}").json()
    a = d["assessments"][0]
    known = {
        "Which principle limits the blast radius of a compromised account?": "Least privilege",
        "What combines likelihood and impact?": "risk",
        "Encryption of data at rest primarily protects:": "Confidentiality",
    }
    good = {q["id"]: known.get(q["prompt"], (q["choices"][0] if q["choices"] else "x"))
            for q in a["questions"]}
    r = admin.post(f"/api/assessments/{a['id']}/submit", json={"answers": good}).json()
    assert r["passed"] is True and r["score"] >= 70

    bad = {q["id"]: "definitely-wrong" for q in a["questions"]}
    r2 = admin.post(f"/api/assessments/{a['id']}/submit", json={"answers": bad}).json()
    assert r2["passed"] is False


def test_competency_tracking(admin):
    # After the above, linux-fundamentals competency should be demonstrated.
    comps = {c["key"]: c["level"] for c in admin.get("/api/competencies").json()["items"]}
    assert comps.get("linux-fundamentals", 0) >= 1


def test_skills_dashboard(admin):
    d = admin.get("/api/skills").json()
    assert "domains" in d and len(d["domains"]) > 5


def test_prerequisite_status_reported(admin):
    d = admin.get("/api/courses/advanced-web-security").json()
    assert "prerequisite_status" in d
    # advanced course: prerequisites likely unmet for a fresh admin
    assert "met" in d["prerequisite_status"]


def test_hints_are_optional_and_tracked(admin):
    d = admin.get("/api/courses/linux-fundamentals").json()
    lesson = next(l for l in d["lessons"] if l["has_hints"])
    r = admin.get(f"/api/lessons/{lesson['id']}/hint?index=0")
    assert r.status_code == 200 and r.json()["text"]


def test_walkthrough_optional(admin):
    d = admin.get("/api/courses/linux-fundamentals").json()
    lesson = next(l for l in d["lessons"] if l["has_walkthrough"])
    r = admin.get(f"/api/lessons/{lesson['id']}/walkthrough")
    assert r.status_code == 200 and len(r.json()["steps"]) >= 1


def test_hints_can_be_disabled(admin):
    admin.put("/api/settings/ui.hints_enabled", json={"value": False})
    d = admin.get("/api/courses/linux-fundamentals").json()
    lesson = next(l for l in d["lessons"] if l["has_hints"])
    r = admin.get(f"/api/lessons/{lesson['id']}/hint?index=0")
    assert r.status_code == 403
    admin.put("/api/settings/ui.hints_enabled", json={"value": True})


def test_recommendations(admin):
    r = admin.get("/api/recommendations").json()
    assert len(r["items"]) >= 1
    assert "reasons" in r["items"][0]
