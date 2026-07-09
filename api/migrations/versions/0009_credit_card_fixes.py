"""cartão: pagamento de fatura neutro + sinal correto das compras

Revision ID: 0009_credit_card_fixes
Revises: 0008_investments
Create Date: 2026-07-08

"""
from collections.abc import Sequence

from alembic import op

revision: str = "0009_credit_card_fixes"
down_revision: str | None = "0008_investments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Pagamento de fatura de cartão é quitação de dívida, não gasto novo (a
    # compra já conta). Aparece nas duas pernas (conta + cartão) → neutro evita
    # o gasto duplicado.
    op.execute(
        "UPDATE transactions SET is_transfer = true "
        "WHERE lower(raw->>'category') = 'credit card payment'"
    )
    # No cartão o Pluggy usa sinal invertido (compra = valor positivo, pois
    # aumenta a fatura). Uma compra é GASTO: inverte sinal e direção para as
    # transações já importadas de contas de cartão.
    op.execute(
        """
        UPDATE transactions t
        SET amount = -t.amount,
            direction = CASE WHEN t.direction = 'in' THEN 'out' ELSE 'in' END
        FROM accounts a
        WHERE t.account_id = a.id AND a.type = 'credit_card'
        """
    )
    # Após a inversão, reduções de fatura (pagamento/estorno) ficam positivas
    # (in) — não são receita: marca como neutras para não inflar o Entrou.
    op.execute(
        """
        UPDATE transactions t SET is_transfer = true
        FROM accounts a
        WHERE t.account_id = a.id AND a.type = 'credit_card'
          AND t.direction = 'in'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE transactions t
        SET amount = -t.amount,
            direction = CASE WHEN t.direction = 'in' THEN 'out' ELSE 'in' END
        FROM accounts a
        WHERE t.account_id = a.id AND a.type = 'credit_card'
        """
    )
    op.execute(
        "UPDATE transactions SET is_transfer = false "
        "WHERE lower(raw->>'category') = 'credit card payment'"
    )
