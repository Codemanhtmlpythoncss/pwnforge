"""Authentication and authorisation."""
from __future__ import annotations


def test_bootstrap_then_second_bootstrap_rejected(admin):
    r = admin.post("/api/auth/bootstrap", json={"username": "another", "password": "yyyyyyyyyy"})
    assert r.status_code == 409  # already initialised


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "root", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    from fastapi.testclient import TestClient
    from backend.app.main import create_app
    fresh = TestClient(create_app())
    assert fresh.get("/api/auth/me").status_code == 401


def test_learner_cannot_access_admin(learner):
    assert learner.get("/api/settings").status_code == 403
    assert learner.get("/api/users").status_code == 403
    assert learner.get("/api/audit").status_code == 403


def test_admin_can_access_admin(admin):
    assert admin.get("/api/settings").status_code == 200
    assert admin.get("/api/users").status_code == 200


def test_password_hash_not_leaked(admin):
    me = admin.get("/api/auth/me").json()["user"]
    assert "password" not in me and "password_hash" not in me


def test_account_reset_clears_all_progress_but_keeps_account(admin):
    from backend.tests.conftest import make_user
    from backend.app.database.base import session_scope
    from backend.app.database.models import (
        Achievement, Assessment, AssessmentProgress, Certificate, Course, CourseProgress,
        Flag, FlagSubmission, LearningPath, Lesson, LessonProgress, User, UserAchievement,
        UserCompetency,
    )

    learner, info = make_user(admin)
    with session_scope() as db:
        user = db.query(User).filter_by(username=info["username"]).one()
        course = db.query(Course).first()
        lesson = db.query(Lesson).first()
        assessment = db.query(Assessment).first()
        flag = db.query(Flag).first()
        achievement = db.query(Achievement).first()
        path = db.query(LearningPath).first()
        assert all((course, lesson, assessment, flag, achievement, path))
        user.xp, user.streak_days, user.last_active_day = 420, 3, "2026-10-19"
        db.add_all([
            CourseProgress(user_id=user.id, course_id=course.id),
            LessonProgress(user_id=user.id, lesson_id=lesson.id),
            AssessmentProgress(user_id=user.id, assessment_id=assessment.id, xp_awarded=True),
            UserCompetency(user_id=user.id, competency_key="linux", level=2, evidence_count=4),
            FlagSubmission(user_id=user.id, flag_id=flag.id, correct=True),
            UserAchievement(user_id=user.id, achievement_key=achievement.key),
            Certificate(user_id=user.id, path_id=path.id, serial="PF-RESET-TEST", path_title=path.title),
        ])

    response = learner.post("/api/auth/account/reset")
    assert response.status_code == 200, response.text
    assert learner.get("/api/auth/me").json()["user"]["xp"] == 0
    with session_scope() as db:
        user = db.query(User).filter_by(username=info["username"]).one()
        assert (user.xp, user.streak_days, user.last_active_day) == (0, 0, None)
        for model in (CourseProgress, LessonProgress, AssessmentProgress, UserCompetency,
                      FlagSubmission, UserAchievement, Certificate):
            assert db.query(model).filter_by(user_id=user.id).count() == 0


def test_no_password_minimum_unless_an_admin_sets_one(admin):
    # By default any password that isn't empty is accepted.
    assert admin.post("/api/users", json={"username": "shorty", "password": "x", "role": "learner"}).status_code == 200
    assert admin.post("/api/users", json={"username": "empty1", "password": "", "role": "learner"}).status_code == 422
    # An administrator can still ask for a minimum.
    admin.put("/api/settings/auth.min_password_length", json={"value": 10})
    r = admin.post("/api/users", json={"username": "shorty2", "password": "ninechar9", "role": "learner"})
    assert r.status_code == 400
    admin.put("/api/settings/auth.min_password_length", json={"value": 1})
