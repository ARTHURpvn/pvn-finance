"""categories — taxonomia + seed de categorias de sistema (F3 / FR-014)

Revision ID: 0003_categories
Revises: 0002_users
Create Date: 2026-06-18

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.domain.category import SYSTEM_CATEGORIES

revision: str = "0003_categories"
down_revision: str | None = "0002_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column(
            "is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    # Seed das categorias de sistema (user_id NULL, is_system TRUE).
    categories = sa.table(
        "categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("user_id", postgresql.UUID(as_uuid=True)),
        sa.column("parent_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("kind", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    op.bulk_insert(
        categories,
        [
            {
                "id": uuid.uuid4(),
                "user_id": None,
                "parent_id": None,
                "name": name,
                "kind": kind.value,
                "is_system": True,
            }
            for name, kind in SYSTEM_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
