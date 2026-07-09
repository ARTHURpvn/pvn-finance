"""fluxo de caixa: pagamento de fatura na conta conta como gasto

Revision ID: 0010_cash_flow_bill
Revises: 0009_credit_card_fixes
Create Date: 2026-07-09

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0010_cash_flow_bill"
down_revision: str | None = "0009_credit_card_fixes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No modelo de caixa, o pagamento de fatura que SAI da conta de depósito é
    # gasto. A 0009 marcou as duas pernas como neutras; reverte só a perna da
    # conta de depósito (o "PGTO CARTAO"). A perna no cartão ("Pagamento
    # recebido") permanece neutra e o dashboard ignora contas de cartão.
    op.execute(
        """
        UPDATE transactions t SET is_transfer = false
        FROM accounts a
        WHERE t.account_id = a.id
          AND lower(t.raw->>'category') = 'credit card payment'
          AND a.type <> 'credit_card'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE transactions t SET is_transfer = true
        FROM accounts a
        WHERE t.account_id = a.id
          AND lower(t.raw->>'category') = 'credit card payment'
          AND a.type <> 'credit_card'
        """
    )
