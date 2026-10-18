"""api tokens and vpn clients

Revision ID: b7c1d2e3f4a5
Revises: e48b4fd649b1
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c1d2e3f4a5"
down_revision = "e48b4fd649b1"
branch_labels = None
depends_on = None


def _has(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # (a database made by `pwnforge init` already has every table: only create what's missing)
    if not _has("api_tokens"):
        op.create_table(
            "api_tokens",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(80), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("hint", sa.String(12), nullable=False),
            sa.Column("scopes", sa.JSON, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.Column("last_used_at", sa.DateTime(timezone=True)),
            sa.Column("revoked", sa.Boolean, nullable=False),
        )
        op.create_index("ix_api_tokens_user_id", "api_tokens", ["user_id"])
    if not _has("vpn_clients"):
        op.create_table(
            "vpn_clients",
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("serial", sa.String(64), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True)),
            sa.Column("downloaded_at", sa.DateTime(timezone=True)),
            sa.Column("revoked_at", sa.DateTime(timezone=True)),
            sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        )
        op.create_index("ix_vpn_clients_user_id", "vpn_clients", ["user_id"])


def downgrade() -> None:
    op.drop_table("vpn_clients")
    op.drop_table("api_tokens")
