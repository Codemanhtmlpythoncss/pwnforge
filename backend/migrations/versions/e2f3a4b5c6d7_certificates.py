"""certificates

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-10-19

A certificate issued when a learner completes a learning path.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "certificates" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "certificates",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("serial", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path_id", sa.String(length=80), sa.ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("path_title", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "path_id", name="uq_user_path_certificate"),
    )
    op.create_index("ix_certificates_serial", "certificates", ["serial"], unique=True)
    op.create_index("ix_certificates_user_id", "certificates", ["user_id"])


def downgrade() -> None:
    if "certificates" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("certificates")
