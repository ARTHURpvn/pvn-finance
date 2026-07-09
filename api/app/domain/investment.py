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


#: Palavras/subtipos que indicam reserva de resgate imediato (dinheiro
#: disponível a qualquer hora). Conta como SALDO, não como investimento de prazo.
_RESERVE_KEYWORDS = ("rende f", "reserva", "poupan")


def is_liquid_reserve(investment: Investment) -> bool:
    """True se o investimento é uma reserva de liquidez imediata (BB Rende
    Fácil, poupança) — tratada como saldo do banco, não como investimento de
    prazo (CDB, fundo, ação)."""
    name = investment.name.lower()
    if (investment.subtype or "").upper() == "SAVINGS":
        return True
    return any(k in name for k in _RESERVE_KEYWORDS)


def total_reserves(investments: Iterable[Investment]) -> Decimal:
    """Soma as reservas de liquidez imediata (contam como saldo)."""
    return sum(
        (i.balance for i in investments if is_liquid_reserve(i)), Decimal("0")
    )


def total_invested(investments: Iterable[Investment]) -> Decimal:
    """Soma os investimentos de prazo (CDB, fundos) — mostrados à parte, fora
    do saldo total. Exclui as reservas de liquidez (essas são saldo)."""
    return sum(
        (i.balance for i in investments if not is_liquid_reserve(i)), Decimal("0")
    )
