"""Investimento — entidade de domínio. Compõe o patrimônio total."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Investment:
    """Posição de investimento (ex.: BB Rende Fácil, CDB, fundo). O ``balance``
    é o valor atual da posição, somado ao patrimônio total."""

    id: UUID
    user_id: UUID
    connection_id: UUID
    provider_investment_id: str
    name: str
    type: str
    balance: Decimal
    currency: str = "BRL"
    subtype: str | None = None


def total_invested(investments: Iterable[Investment]) -> Decimal:
    """Soma o valor atual de todos os investimentos (parte do patrimônio)."""
    return sum((inv.balance for inv in investments), Decimal("0"))
