"""Transação — entidade de domínio + sinal (RN-01) e imutabilidade (RN-04)."""

from dataclasses import dataclass, replace
from datetime import date as date_type
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class Direction(StrEnum):
    IN = "in"
    OUT = "out"

    @classmethod
    def from_amount(cls, amount: Decimal) -> "Direction":
        """RN-01: crédito (amount ≥ 0) é entrada; débito (< 0) é saída."""
        return cls.IN if amount >= 0 else cls.OUT


#: Categorias do agregador que são movimentação do próprio dinheiro — não
#: gasto nem receita, portanto neutras no fluxo (Entrou/Saiu):
#: - investimento próprio (aplicação/resgate/proventos) — o valor vive no
#:   patrimônio via os investimentos. Ex.: BB Rende Fácil, Aplicação RDB.
#: - transferência entre contas do mesmo titular. Ex.: PIX de uma conta sua
#:   para outra sua ("Same person transfer").
_FLOW_NEUTRAL_CATEGORIES = frozenset(
    {
        "automatic investment",
        "investments",
        "proceeds interests and dividends",
        "same person transfer",
    }
)


def is_flow_neutral(provider_category: str | None) -> bool:
    """True se a categoria do agregador indica movimentação do próprio dinheiro
    (investimento ou transferência entre contas próprias), que deve ser
    desconsiderada de Entrou/Saiu."""
    return (
        provider_category is not None
        and provider_category.strip().lower() in _FLOW_NEUTRAL_CATEGORIES
    )


@dataclass(frozen=True, slots=True)
class Transaction:
    """Lançamento de uma conta. Imutável após import (RN-04): só a categoria
    pode mudar, via :meth:`recategorize`, que devolve uma nova instância."""

    id: UUID
    user_id: UUID
    account_id: UUID
    provider_transaction_id: str
    date: date_type
    amount: Decimal
    direction: Direction
    description: str
    counterpart: str | None = None
    category_id: UUID | None = None
    # Movimentação de investimento próprio (aplicação/resgate) — neutra no
    # fluxo de Entrou/Saiu. O valor é representado no patrimônio via investimentos.
    is_transfer: bool = False

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        user_id: UUID,
        account_id: UUID,
        provider_transaction_id: str,
        date: date_type,
        amount: Decimal,
        description: str,
        counterpart: str | None = None,
        category_id: UUID | None = None,
        is_transfer: bool = False,
    ) -> "Transaction":
        """Cria uma transação derivando o sinal do amount (RN-01)."""
        return cls(
            id=id,
            user_id=user_id,
            account_id=account_id,
            provider_transaction_id=provider_transaction_id,
            date=date,
            amount=amount,
            direction=Direction.from_amount(amount),
            description=description,
            counterpart=counterpart,
            category_id=category_id,
            is_transfer=is_transfer,
        )

    def recategorize(self, category_id: UUID) -> "Transaction":
        """RN-04: devolve nova transação alterando somente ``category_id``."""
        return replace(self, category_id=category_id)
