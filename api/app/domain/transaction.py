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
        )

    def recategorize(self, category_id: UUID) -> "Transaction":
        """RN-04: devolve nova transação alterando somente ``category_id``."""
        return replace(self, category_id=category_id)
