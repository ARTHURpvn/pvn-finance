"""rules — motor de regras de categorização (F7 / FR-015)

Revision ID: 0005_rules
Revises: 0004_sync
Create Date: 2026-06-18

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_rules"
down_revision: str | None = "0004_sync"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_type", sa.String(length=20), nullable=False),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "priority", sa.Integer(), server_default="100", nullable=False
        ),
    )
    op.create_index("ix_rules_user_id", "rules", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_rules_user_id", table_name="rules")
    op.drop_table("rules")
