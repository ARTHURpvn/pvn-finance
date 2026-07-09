"""investments + transactions.is_transfer (patrimônio com investimentos)

Revision ID: 0008_investments
Revises: 0007_scale_indexes
Create Date: 2026-07-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_investments"
down_revision: str | None = "0007_scale_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_investment_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("subtype", sa.String(50), nullable=True),
        sa.Column("balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "connection_id",
            "provider_investment_id",
            name="uq_investments_connection_provider",
        ),
    )
    op.create_index("ix_investments_user_id", "investments", ["user_id"])

    # Flag de movimentação de investimento próprio (neutra no fluxo Entrou/Saiu).
    op.add_column(
        "transactions",
        sa.Column(
            "is_transfer",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    # Backfill das transações já importadas, pela categoria do agregador (raw).
    op.execute(
        """
        UPDATE transactions SET is_transfer = true
        WHERE lower(raw->>'category') IN (
            'automatic investment', 'investments',
            'proceeds interests and dividends'
        )
        """
    )
    op.create_index(
        "ix_transactions_user_transfer_date",
        "transactions",
        ["user_id", "is_transfer", "date"],
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_user_transfer_date", table_name="transactions")
    op.drop_column("transactions", "is_transfer")
    op.drop_index("ix_investments_user_id", table_name="investments")
    op.drop_table("investments")
