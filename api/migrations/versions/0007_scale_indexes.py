"""índices de escala (F4) — busca textual, categoria, worker; remove redundante

Revision ID: 0007_scale_indexes
Revises: 0006_refresh_tokens
Create Date: 2026-07-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_scale_indexes"
down_revision: str | None = "0006_refresh_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Busca textual do extrato (description ILIKE '%q%') — sem isto é seq scan.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        "ix_transactions_description_trgm",
        "transactions",
        ["description"],
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )
    # Filtro por categoria no extrato/dashboard.
    op.create_index(
        "ix_transactions_user_category_date",
        "transactions",
        ["user_id", "category_id", "date"],
    )
    # Varredura do worker: só conexões ativas "devidas" (índice parcial).
    op.create_index(
        "ix_connections_due",
        "connections",
        ["last_sync_at"],
        postgresql_where=sa.text("status = 'ativa'"),
    )
    # Redundante: coberto pelo prefixo da unique (connection_id, provider_account_id).
    op.drop_index("ix_accounts_connection_id", table_name="accounts")


def downgrade() -> None:
    op.create_index("ix_accounts_connection_id", "accounts", ["connection_id"])
    op.drop_index("ix_connections_due", table_name="connections")
    op.drop_index("ix_transactions_user_category_date", table_name="transactions")
    op.drop_index("ix_transactions_description_trgm", table_name="transactions")
    # A extensão pg_trgm é deixada instalada (pode ser usada por outros objetos).
