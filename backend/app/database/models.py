"""SQLAlchemy ORM models for Pwnforge.

Content (courses, lessons, profiles, labs, paths) is imported from the
versioned ``catalog/`` definitions into these tables so the API can paginate,
filter and search it efficiently. Learner state (progress, competencies,
achievements, submissions) and infrastructure state (VM instances, networks,
snapshots, jobs) live only in the database.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


# --------------------------------------------------------------------------
# Enumerations
# --------------------------------------------------------------------------
class Difficulty(str, enum.Enum):
    orientation = "orientation"       # Level 0
    beginner = "beginner"             # Level 1
    easy = "easy"                     # Level 2
    intermediate = "intermediate"     # Level 3
    hard = "hard"                     # Level 4
    advanced = "advanced"             # Level 5
    expert = "expert"                 # Level 6
    mastery = "mastery"               # Level 7

    @property
    def level(self) -> int:
        return {
            "orientation": 0, "beginner": 1, "easy": 2, "intermediate": 3,
            "hard": 4, "advanced": 5, "expert": 6, "mastery": 7,
        }[self.value]


class UserRole(str, enum.Enum):
    administrator = "administrator"
    instructor = "instructor"
    learner = "learner"
    viewer = "viewer"


class ProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class ProfileReadiness(str, enum.Enum):
    ready = "ready"                       # base image present, launchable now
    requires_base_image = "requires_base_image"
    requires_install_media = "requires_install_media"
    requires_manual_config = "requires_manual_config"
    unsupported_on_host = "unsupported_on_host"
    invalid = "invalid"
    failed_provisioning = "failed_provisioning"


class ImageStatus(str, enum.Enum):
    absent = "absent"            # recorded, not downloaded/built (metadata only)
    downloading = "downloading"
    building = "building"
    present = "present"          # on disk, checksum verified
    corrupt = "corrupt"
    unverified = "unverified"    # on disk, checksum not yet confirmed


class VMStatus(str, enum.Enum):
    defined = "defined"
    creating = "creating"
    starting = "starting"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    paused = "paused"
    resetting = "resetting"
    error = "error"
    deleting = "deleting"
    deleted = "deleted"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class NetworkMode(str, enum.Enum):
    isolated = "isolated"
    nat = "nat"
    hostonly = "hostonly"


# --------------------------------------------------------------------------
# Identity & access
# --------------------------------------------------------------------------
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.learner)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_specialization: Mapped[str | None] = mapped_column(String(64))
    xp: Mapped[int] = mapped_column(Integer, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_day: Mapped[str | None] = mapped_column(String(10))  # YYYY-MM-DD

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """Server-side session record enabling revocation of signed cookies."""
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    user_agent: Mapped[str | None] = mapped_column(String(256))
    ip: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="sessions")


# --------------------------------------------------------------------------
# Learning content
# --------------------------------------------------------------------------
class Competency(Base):
    __tablename__ = "competencies"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    domain: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)  # slug
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    specialization: Mapped[str | None] = mapped_column(String(64), index=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=60)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)   # course ids
    competency_prereqs: Mapped[list] = mapped_column(JSON, default=list)  # competency keys
    tags: Mapped[list] = mapped_column(JSON, default=list)
    references: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    os_requirements: Mapped[list] = mapped_column(JSON, default=list)
    lab_id: Mapped[str | None] = mapped_column(String(80))

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Lesson.order"
    )
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty))
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    competency_key: Mapped[str | None] = mapped_column(String(80))
    # Optional scaffolding (hidden until the learner opts in):
    hints: Mapped[list] = mapped_column(JSON, default=list)        # [{text, cost}]
    walkthrough: Mapped[list] = mapped_column(JSON, default=list)  # [{step, title, detail}]

    course: Mapped[Course] = relationship(back_populates="lessons")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="Exercise.order"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(140), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text, default="")
    # mcq | short_answer | command | configuration | flag | lab_check
    kind: Mapped[str] = mapped_column(String(32), default="short_answer")
    spec: Mapped[dict] = mapped_column(JSON, default=dict)  # choices, answer hash, checks
    points: Mapped[int] = mapped_column(Integer, default=10)
    competency_key: Mapped[str | None] = mapped_column(String(80))
    explanation: Mapped[str] = mapped_column(Text, default="")
    hints: Mapped[list] = mapped_column(JSON, default=list)
    walkthrough: Mapped[list] = mapped_column(JSON, default=list)

    lesson: Mapped[Lesson] = relationship(back_populates="exercises")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    passing_score: Mapped[int] = mapped_column(Integer, default=70)  # percent
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty))
    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan",
        order_by="AssessmentQuestion.order",
    )
    course: Mapped[Course] = relationship(back_populates="assessments")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[str] = mapped_column(String(140), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    order: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(32), default="mcq")
    prompt: Mapped[str] = mapped_column(Text)
    choices: Mapped[list] = mapped_column(JSON, default=list)   # for mcq (no answer flag leaked)
    answer_hash: Mapped[str | None] = mapped_column(String(128))  # server-side validation
    points: Mapped[int] = mapped_column(Integer, default=10)
    competency_key: Mapped[str | None] = mapped_column(String(80))
    explanation: Mapped[str] = mapped_column(Text, default="")
    hints: Mapped[list] = mapped_column(JSON, default=list)

    assessment: Mapped["Assessment"] = relationship(back_populates="questions")


class LearningPath(TimestampMixin, Base):
    __tablename__ = "learning_paths"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    specialization: Mapped[str | None] = mapped_column(String(64), index=True)
    difficulty_min: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.beginner)
    difficulty_max: Mapped[Difficulty] = mapped_column(Enum(Difficulty), default=Difficulty.expert)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    steps: Mapped[list["LearningPathStep"]] = relationship(
        back_populates="path", cascade="all, delete-orphan", order_by="LearningPathStep.order"
    )


class LearningPathStep(Base):
    __tablename__ = "learning_path_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    path_id: Mapped[str] = mapped_column(ForeignKey("learning_paths.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    course_id: Mapped[str | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"))
    lab_id: Mapped[str | None] = mapped_column(String(80))
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(Text, default="")

    path: Mapped[LearningPath] = relationship(back_populates="steps")


# --------------------------------------------------------------------------
# Learner state
# --------------------------------------------------------------------------
class CourseProgress(Base):
    __tablename__ = "course_progress"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_course_progress"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus), default=ProgressStatus.not_started)
    percent: Mapped[float] = mapped_column(Float, default=0.0)
    best_assessment_score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus), default=ProgressStatus.not_started)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    walkthrough_opened: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserCompetency(Base):
    __tablename__ = "user_competencies"
    __table_args__ = (UniqueConstraint("user_id", "competency_key", name="uq_user_competency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    competency_key: Mapped[str] = mapped_column(String(80), index=True)
    # 0 not started, 1 beginner, 2 easy, 3 intermediate, 4 advanced/mastered
    level: Mapped[int] = mapped_column(Integer, default=0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_demonstrated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Achievement(Base):
    __tablename__ = "achievements"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="general")
    points: Mapped[int] = mapped_column(Integer, default=10)
    icon: Mapped[str] = mapped_column(String(64), default="trophy")
    criteria: Mapped[dict] = mapped_column(JSON, default=dict)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_key", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_key: Mapped[str] = mapped_column(ForeignKey("achievements.key", ondelete="CASCADE"))
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "kind", "ref_id", name="uq_bookmark"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32))   # course | profile | lab
    ref_id: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# --------------------------------------------------------------------------
# Virtualisation content & state
# --------------------------------------------------------------------------
class BaseImage(TimestampMixin, Base):
    __tablename__ = "base_images"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    os_family: Mapped[str] = mapped_column(String(40), index=True)  # debian, kali, ubuntu, windows...
    os_version: Mapped[str] = mapped_column(String(40))
    arch: Mapped[str] = mapped_column(String(20), default="x86_64")
    source: Mapped[str] = mapped_column(Text, default="")           # URL or build recipe ref
    source_kind: Mapped[str] = mapped_column(String(20), default="qcow2")  # qcow2 | iso | build
    checksum: Mapped[str | None] = mapped_column(String(160))
    checksum_algo: Mapped[str] = mapped_column(String(16), default="sha256")
    format: Mapped[str] = mapped_column(String(16), default="qcow2")
    parent_key: Mapped[str | None] = mapped_column(ForeignKey("base_images.key"))
    virtual_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    actual_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ImageStatus] = mapped_column(Enum(ImageStatus), default=ImageStatus.absent)
    path: Mapped[str | None] = mapped_column(String(512))
    build_instructions: Mapped[str] = mapped_column(Text, default="")
    immutable: Mapped[bool] = mapped_column(Boolean, default=True)


class VMProfile(TimestampMixin, Base):
    __tablename__ = "vm_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), index=True)
    os_family: Mapped[str] = mapped_column(String(40), index=True)
    arch: Mapped[str] = mapped_column(String(20), default="x86_64", index=True)
    base_image_key: Mapped[str | None] = mapped_column(ForeignKey("base_images.key"))
    vcpu: Mapped[int] = mapped_column(Integer, default=1)
    memory_mb: Mapped[int] = mapped_column(Integer, default=1024)
    disk_gb: Mapped[int] = mapped_column(Integer, default=10)
    network_mode: Mapped[NetworkMode] = mapped_column(Enum(NetworkMode), default=NetworkMode.isolated)
    packages: Mapped[list] = mapped_column(JSON, default=list)
    services: Mapped[list] = mapped_column(JSON, default=list)
    provisioning: Mapped[dict] = mapped_column(JSON, default=dict)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=45)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    reset_supported: Mapped[bool] = mapped_column(Boolean, default=True)
    snapshots_supported: Mapped[bool] = mapped_column(Boolean, default=True)
    disposable: Mapped[bool] = mapped_column(Boolean, default=True)
    readiness: Mapped[ProfileReadiness] = mapped_column(
        Enum(ProfileReadiness), default=ProfileReadiness.requires_base_image, index=True
    )
    lab_id: Mapped[str | None] = mapped_column(String(80), index=True)
    course_ids: Mapped[list] = mapped_column(JSON, default=list)

    __table_args__ = (
        Index("ix_profile_cat_diff", "category", "difficulty"),
        Index("ix_profile_os_arch", "os_family", "arch"),
    )


class VMInstance(TimestampMixin, Base):
    __tablename__ = "vm_instances"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(160), index=True)
    profile_id: Mapped[str | None] = mapped_column(ForeignKey("vm_profiles.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lab_instance_id: Mapped[str | None] = mapped_column(
        ForeignKey("lab_instances.id", ondelete="CASCADE"), index=True
    )
    driver: Mapped[str] = mapped_column(String(20), default="simulation")
    driver_ref: Mapped[str | None] = mapped_column(String(128))  # libvirt domain name etc.
    status: Mapped[VMStatus] = mapped_column(Enum(VMStatus), default=VMStatus.defined, index=True)
    base_image_key: Mapped[str | None] = mapped_column(String(80))
    overlay_path: Mapped[str | None] = mapped_column(String(512))
    vcpu: Mapped[int] = mapped_column(Integer, default=1)
    memory_mb: Mapped[int] = mapped_column(Integer, default=1024)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    network_id: Mapped[str | None] = mapped_column(String(32))
    vnc_port: Mapped[int | None] = mapped_column(Integer)
    disposable: Mapped[bool] = mapped_column(Boolean, default=True)
    persistent: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class Lab(TimestampMixin, Base):
    __tablename__ = "labs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    machines: Mapped[list] = mapped_column(JSON, default=list)      # [{role, profile_id, ip}]
    networks: Mapped[list] = mapped_column(JSON, default=list)      # [{name, cidr, mode}]
    startup_order: Mapped[list] = mapped_column(JSON, default=list)
    readiness_checks: Mapped[list] = mapped_column(JSON, default=list)
    course_id: Mapped[str | None] = mapped_column(String(80))
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=90)
    reset_behavior: Mapped[str] = mapped_column(String(32), default="disposable")
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)


class LabInstance(TimestampMixin, Base):
    __tablename__ = "lab_instances"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    lab_id: Mapped[str] = mapped_column(ForeignKey("labs.id"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[VMStatus] = mapped_column(Enum(VMStatus), default=VMStatus.defined, index=True)
    network_ids: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class VirtualNetwork(TimestampMixin, Base):
    __tablename__ = "virtual_networks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), index=True)
    mode: Mapped[NetworkMode] = mapped_column(Enum(NetworkMode), default=NetworkMode.isolated)
    cidr: Mapped[str | None] = mapped_column(String(64))
    driver_ref: Mapped[str | None] = mapped_column(String(128))
    lab_instance_id: Mapped[str | None] = mapped_column(
        ForeignKey("lab_instances.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    external_access: Mapped[bool] = mapped_column(Boolean, default=False)


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    vm_instance_id: Mapped[str] = mapped_column(
        ForeignKey("vm_instances.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(16), default="disk")  # disk | memory | both
    driver_ref: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ResourceReservation(Base):
    __tablename__ = "resource_reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    vm_instance_id: Mapped[str] = mapped_column(
        ForeignKey("vm_instances.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    vcpu: Mapped[int] = mapped_column(Integer, default=1)
    memory_mb: Mapped[int] = mapped_column(Integer, default=1024)
    disk_gb: Mapped[int] = mapped_column(Integer, default=10)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# --------------------------------------------------------------------------
# Jobs, flags, audit, settings
# --------------------------------------------------------------------------
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(48), index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64), index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(120), default="")
    steps: Mapped[list] = mapped_column(JSON, default=list)   # [{stage, status, ts, detail}]
    error: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Flag(Base):
    """A submittable flag. Only a salted hash of the value is stored."""
    __tablename__ = "flags"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(32), index=True)  # lab | profile | exercise
    scope_id: Mapped[str] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(120), default="flag")
    value_hash: Mapped[str] = mapped_column(String(128))
    points: Mapped[int] = mapped_column(Integer, default=25)
    order: Mapped[int] = mapped_column(Integer, default=0)
    competency_key: Mapped[str | None] = mapped_column(String(80))


class FlagSubmission(Base):
    __tablename__ = "flag_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    flag_id: Mapped[str] = mapped_column(ForeignKey("flags.id", ondelete="CASCADE"), index=True)
    correct: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str | None] = mapped_column(String(48))
    target_id: Mapped[str | None] = mapped_column(String(120))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)  # never contains secrets
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class Setting(Base):
    """Runtime-editable settings. Every key has a real backend consumer."""
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON)
    category: Mapped[str] = mapped_column(String(48), default="general", index=True)
    value_type: Mapped[str] = mapped_column(String(20), default="string")
    description: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


# --------------------------------------------------------------------------
# Public API credentials and remote access
# --------------------------------------------------------------------------
class ApiToken(Base):
    """A personal API token for /api/v1 and /api/ai. Only a SHA-256 hash of the
    secret is stored; the full token is shown once when it is created."""
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    token_hash: Mapped[str] = mapped_column(String(64))
    hint: Mapped[str] = mapped_column(String(12))          # last characters, to recognise it
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class VpnClient(Base):
    """An OpenVPN client certificate issued by Pwnforge's own CA. The private key
    leaves the server once, inside the profile the owner downloads."""
    __tablename__ = "vpn_clients"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    serial: Mapped[str] = mapped_column(String(64), unique=True)   # hex certificate serial
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
