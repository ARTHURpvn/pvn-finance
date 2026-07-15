"""Detalhe dos investimentos: aplicado, lucro, taxa, vencimento, instituição.

Campos que o Pluggy retorna em /investments mas que a gente descartava — base
para renda fixa mensal, ganho/perda, evolução e agrupamento por banco.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_investment_detail"
down_revision: str | None = "0010_cash_flow_bill"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = [
    sa.Column("amount_original", sa.Numeric(18, 2), nullable=True),
    sa.Column("amount_profit", sa.Numeric(18, 2), nullable=True),
    sa.Column("value", sa.Numeric(18, 6), nullable=True),
    sa.Column("quantity", sa.Numeric(18, 6), nullable=True),
    sa.Column("rate", sa.Numeric(10, 4), nullable=True),
    sa.Column("rate_type", sa.String(30), nullable=True),
    sa.Column("annual_rate", sa.Numeric(10, 4), nullable=True),
    sa.Column("last_month_rate", sa.Numeric(10, 4), nullable=True),
    sa.Column("last_twelve_months_rate", sa.Numeric(10, 4), nullable=True),
    sa.Column("due_date", sa.Date(), nullable=True),
    sa.Column("purchase_date", sa.Date(), nullable=True),
    sa.Column("institution", sa.String(255), nullable=True),
]


def upgrade() -> None:
    for col in _COLUMNS:
        op.add_column("investments", col)


def downgrade() -> None:
    for col in reversed(_COLUMNS):
        op.drop_column("investments", col.name)
