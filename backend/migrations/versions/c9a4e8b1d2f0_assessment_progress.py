"""Track assessment progress and one-time XP rewards.

Revision ID: c9a4e8b1d2f0
Revises: b7c1d2e3f4a5
Create Date: 2026-10-19
"""
from alembic import op
import sqlalchemy as sa


revision = "c9a4e8b1d2f0"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "assessment_progress" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "assessment_progress",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(),
                      sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("assessment_id", sa.String(length=120),
                      sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("best_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("xp_awarded", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("user_id", "assessment_id",
                                name="uq_assessment_progress_user_assessment"),
        )
        op.create_index("ix_assessment_progress_user_id", "assessment_progress", ["user_id"])
        op.create_index("ix_assessment_progress_assessment_id", "assessment_progress",
                        ["assessment_id"])

    # Before this migration each passing submission paid XP. Preserve that fact
    # for learners who already passed, so an update cannot pay them again.
    op.execute(sa.text("""
        INSERT INTO assessment_progress
            (user_id, assessment_id, best_score, passed, xp_awarded)
        SELECT cp.user_id, a.id, cp.best_assessment_score, TRUE, TRUE
          FROM course_progress AS cp
          JOIN assessments AS a ON a.course_id = cp.course_id
         WHERE cp.best_assessment_score >= (a.passing_score / 100.0)
           AND NOT EXISTS (
               SELECT 1 FROM assessment_progress AS ap
                WHERE ap.user_id = cp.user_id AND ap.assessment_id = a.id
           )
    """))


def downgrade() -> None:
    op.drop_table("assessment_progress")
