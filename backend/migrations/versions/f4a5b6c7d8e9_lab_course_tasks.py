"""course-style tasks for guided labs

Revision ID: f4a5b6c7d8e9
Revises: e2f3a4b5c6d7
Create Date: 2026-10-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f4a5b6c7d8e9"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "labs" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("labs")}
        if "tasks" not in columns:
            op.add_column("labs", sa.Column("tasks", sa.JSON(), nullable=False, server_default="[]"))
    if "learning_paths" in inspector.get_table_names():
        path_columns = {column["name"] for column in inspector.get_columns("learning_paths")}
        if "outcomes" not in path_columns:
            op.add_column("learning_paths", sa.Column("outcomes", sa.JSON(), nullable=False, server_default="[]"))
        if "capstone" not in path_columns:
            op.add_column("learning_paths", sa.Column("capstone", sa.JSON(), nullable=False, server_default="{}"))
    if "lab_task_submissions" not in inspector.get_table_names():
        op.create_table(
            "lab_task_submissions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("lab_id", sa.String(length=80), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("task_id", sa.String(length=80), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "lab_id", "task_id",
                                name="uq_lab_task_submission_user_lab_task"),
        )
        op.create_index("ix_lab_task_submissions_user_id", "lab_task_submissions", ["user_id"])
        op.create_index("ix_lab_task_submissions_lab_id", "lab_task_submissions", ["lab_id"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "lab_task_submissions" in tables:
        op.drop_index("ix_lab_task_submissions_lab_id", table_name="lab_task_submissions")
        op.drop_index("ix_lab_task_submissions_user_id", table_name="lab_task_submissions")
        op.drop_table("lab_task_submissions")
    if "labs" in tables:
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("labs")}
        if "tasks" in columns:
            op.drop_column("labs", "tasks")
    if "learning_paths" in tables:
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("learning_paths")}
        if "capstone" in columns:
            op.drop_column("learning_paths", "capstone")
        if "outcomes" in columns:
            op.drop_column("learning_paths", "outcomes")
