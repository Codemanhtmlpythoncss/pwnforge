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


def test_resubmitting_a_passed_assessment_awards_xp_only_once(admin):
    from backend.tests.conftest import make_user

    learner, _ = make_user(admin)
    course = learner.get("/api/courses/cybersecurity-fundamentals").json()
    assessment = course["assessments"][0]
    known = {
        "Which principle limits the blast radius of a compromised account?": "Least privilege",
        "What combines likelihood and impact?": "risk",
        "Encryption of data at rest primarily protects:": "Confidentiality",
    }
    answers = {q["id"]: known[q["prompt"]] for q in assessment["questions"]}
    before = learner.get("/api/auth/me").json()["user"]["xp"]
    first = learner.post(f"/api/assessments/{assessment['id']}/submit", json={"answers": answers})
    assert first.status_code == 200 and first.json()["passed"] is True
    after_first = learner.get("/api/auth/me").json()["user"]["xp"]
    second = learner.post(f"/api/assessments/{assessment['id']}/submit", json={"answers": answers})
    assert second.status_code == 200 and second.json()["passed"] is True
    after_second = learner.get("/api/auth/me").json()["user"]["xp"]
    assert after_first == before + 30
    assert after_second == after_first


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


def test_certificate_issued_on_path_completion(admin):
    from backend.tests.conftest import make_user
    from backend.app.database.base import session_scope
    from backend.app.database.models import CourseProgress, Flag, FlagSubmission, LearningPath, ProgressStatus, User
    learner, info = make_user(admin, "learner")   # a fresh user with no prior progress to collide with
    with session_scope() as s:
        path = next((p for p in s.query(LearningPath).all() if p.steps), None)
        assert path is not None
        pid = path.id
        uid = s.query(User).filter(User.username == info["username"]).first().id
        for st in path.steps:
            if st.course_id:
                s.add(CourseProgress(user_id=uid, course_id=st.course_id, status=ProgressStatus.completed, percent=100))
            if st.lab_id:
                fid = s.query(Flag.id).filter(Flag.scope_type == "lab", Flag.scope_id == st.lab_id).scalar()
                if fid:
                    s.add(FlagSubmission(user_id=uid, flag_id=fid, correct=True))
    r = learner.get(f"/api/paths/{pid}").json()
    assert r["percent"] == 100 and r["certificate"] and r["certificate"]["serial"].startswith("PF-")
    serial = r["certificate"]["serial"]
    assert learner.get(f"/api/paths/{pid}").json()["certificate"]["serial"] == serial   # idempotent
    certs = learner.get("/api/certificates").json()["items"]
    assert any(c["serial"] == serial and c["path_id"] == pid for c in certs)
    assert learner.get(f"/api/certificates/{serial}").json()["path_title"]
    assert learner.get("/api/certificates/PF-NOPE").status_code == 404


def test_learning_paths_resolve_optional_labs_to_friendly_machine_names(admin):
    from backend.app.database.base import session_scope
    from backend.app.database.models import LearningPath

    with session_scope() as db:
        paths = list(db.query(LearningPath).all())
        assert paths
        lab_counts = [sum(step.lab_id is not None for step in path.steps) for path in paths]
        assert all(2 <= count <= 5 for count in lab_counts)
        path_id = next(path.id for path in paths if any(step.lab_id for step in path.steps))

    detail = admin.get(f"/api/paths/{path_id}").json()
    lab_steps = [step for step in detail["steps"] if step["kind"] == "lab"]
    assert lab_steps
    assert all(step["title"] != step["lab_id"] for step in lab_steps)
    assert all(step["difficulty"] for step in lab_steps)
