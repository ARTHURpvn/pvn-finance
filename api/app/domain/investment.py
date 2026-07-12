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


def is_liquid_reserve(investment: Investment) -> bool:
    """True se o investimento é uma reserva de liquidez imediata que conta como
    SALDO do banco — hoje, só poupança de verdade (``subtype == SAVINGS``).

    A "caixinha" BB Rende Fácil, apesar do nome "Reserva", é FUNDO DE
    INVESTIMENTO (``subtype == INVESTMENT_FUND``): é investimento, não saldo
    (decisão do usuário 2026-07-10). Por isso NÃO casamos mais pelo nome
    ("reserva"/"rende fácil"), só pelo subtype de poupança."""
    return (investment.subtype or "").upper() == "SAVINGS"


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
