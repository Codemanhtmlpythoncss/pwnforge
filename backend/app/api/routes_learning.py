"""Courses, learning paths, competencies, progress and bookmarks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api import schemas
from backend.app.api.deps import current_user, current_user_optional, get_db
from backend.app.competencies import service as competencies
from backend.app.core import settings_service as cfg
from backend.app.courses import recommendations
from backend.app.courses import service as courses
from backend.app.database.models import Bookmark, User
from backend.app.learning_paths import service as paths

router = APIRouter(prefix="/api", tags=["learning"])


# ---- Courses ----
@router.get("/courses")
def list_courses(q: str | None = None, category: str | None = None,
                 difficulty: str | None = None, specialization: str | None = None,
                 tag: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                 db: Session = Depends(get_db)) -> dict:
    return courses.list_courses(db, q=q, category=category, difficulty=difficulty,
                                specialization=specialization, tag=tag,
                                limit=limit, offset=offset)


@router.get("/courses/{course_id}")
def course_detail(course_id: str, db: Session = Depends(get_db),
                  user: User | None = Depends(current_user_optional)) -> dict:
    try:
        return courses.get_course_detail(db, course_id, user)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.post("/courses/{course_id}/start")
def start_course(course_id: str, user: User = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    try:
        cp = courses.start_course(db, user, course_id)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))
    return {"status": cp.status.value, "percent": cp.percent}


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: str, body: schemas.CompleteLessonRequest,
                    user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    try:
        return courses.complete_lesson(db, user, lesson_id, body.hints_used,
                                       body.walkthrough_opened)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.get("/lessons/{lesson_id}/hint")
def get_hint(lesson_id: str, index: int = 0, user: User = Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    if not bool(cfg.get_setting(db, "ui.hints_enabled", True)):
        raise HTTPException(403, "Hints are disabled")
    try:
        return courses.reveal_hint(db, user, lesson_id=lesson_id, index=index)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.get("/lessons/{lesson_id}/walkthrough")
def get_walkthrough(lesson_id: str, user: User = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    if not bool(cfg.get_setting(db, "ui.walkthroughs_enabled", True)):
        raise HTTPException(403, "Walkthroughs are disabled")
    try:
        return courses.reveal_walkthrough(db, user, lesson_id)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.get("/exercises/{exercise_id}/hint")
def get_exercise_hint(exercise_id: str, index: int = 0, user: User = Depends(current_user),
                      db: Session = Depends(get_db)) -> dict:
    if not bool(cfg.get_setting(db, "ui.hints_enabled", True)):
        raise HTTPException(403, "Hints are disabled")
    try:
        return courses.reveal_hint(db, user, exercise_id=exercise_id, index=index)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.post("/exercises/{exercise_id}/submit")
def submit_exercise(exercise_id: str, body: schemas.SubmitExerciseRequest,
                    user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    try:
        return courses.submit_exercise(db, user, exercise_id, body.answer)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.post("/assessments/{assessment_id}/submit")
def submit_assessment(assessment_id: str, body: schemas.SubmitAssessmentRequest,
                      user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    try:
        return courses.submit_assessment(db, user, assessment_id, body.answers)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.get("/assessments/{assessment_id}/questions/{question_id}/hint")
def get_assessment_hint(assessment_id: str, question_id: str, index: int = 0,
                        user: User = Depends(current_user),
                        db: Session = Depends(get_db)) -> dict:
    if not bool(cfg.get_setting(db, "ui.hints_enabled", True)):
        raise HTTPException(403, "Hints are disabled")
    try:
        return courses.reveal_assessment_hint(db, assessment_id, question_id, index)
    except courses.CourseError as e:
        raise HTTPException(404, str(e))


@router.get("/recommendations")
def recommend(limit: int = 5, user: User = Depends(current_user),
              db: Session = Depends(get_db)) -> dict:
    return {"items": recommendations.recommend(db, user, limit=limit)}


# ---- Learning paths ----
@router.get("/paths")
def list_paths(db: Session = Depends(get_db)) -> dict:
    return {"items": paths.list_paths(db)}


@router.get("/paths/{path_id}")
def path_detail(path_id: str, db: Session = Depends(get_db),
                user: User | None = Depends(current_user_optional)) -> dict:
    try:
        return paths.path_detail(db, path_id, user)
    except KeyError:
        raise HTTPException(404, "Unknown path")


# ---- Competencies ----
@router.get("/competencies")
def competency_map(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return {"items": competencies.competency_map(db, user.id)}


@router.get("/skills")
def skills_dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    threshold = int(cfg.get_setting(db, "progression.mastery_threshold", 3))
    return competencies.skills_dashboard(db, user.id, threshold)


# ---- Bookmarks ----
@router.get("/bookmarks")
def list_bookmarks(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(Bookmark).where(Bookmark.user_id == user.id)).scalars()
    return {"items": [{"kind": b.kind, "ref_id": b.ref_id} for b in rows]}


@router.post("/bookmarks")
def add_bookmark(body: schemas.BookmarkRequest, user: User = Depends(current_user),
                 db: Session = Depends(get_db)) -> dict:
    existing = db.execute(select(Bookmark).where(
        Bookmark.user_id == user.id, Bookmark.kind == body.kind,
        Bookmark.ref_id == body.ref_id)).scalar_one_or_none()
    if existing is None:
        db.add(Bookmark(user_id=user.id, kind=body.kind, ref_id=body.ref_id))
    return {"ok": True}


@router.delete("/bookmarks")
def remove_bookmark(body: schemas.BookmarkRequest, user: User = Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    existing = db.execute(select(Bookmark).where(
        Bookmark.user_id == user.id, Bookmark.kind == body.kind,
        Bookmark.ref_id == body.ref_id)).scalar_one_or_none()
    if existing:
        db.delete(existing)
    return {"ok": True}
