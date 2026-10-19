"""lab hints and guide

Revision ID: d1e2f3a4b5c6
Revises: c9a4e8b1d2f0
Create Date: 2026-10-19

Adds per-lab tiered hints and a gated walkthrough guide.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d1e2f3a4b5c6"
down_revision = "c9a4e8b1d2f0"
branch_labels = None
depends_on = None


def _cols() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("labs")}


def upgrade() -> None:
    cols = _cols()
    if "hints" not in cols:
        op.add_column("labs", sa.Column("hints", sa.JSON(), nullable=False, server_default="[]"))
    if "guide" not in cols:
        op.add_column("labs", sa.Column("guide", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    cols = _cols()
    if "guide" in cols:
        op.drop_column("labs", "guide")
    if "hints" in cols:
        op.drop_column("labs", "hints")
