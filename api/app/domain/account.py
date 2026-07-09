"""Conta — entidade de domínio + saldo consolidado (RN-02)."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    PAYMENT = "payment"
    CREDIT_CARD = "credit_card"


@dataclass(frozen=True, slots=True)
class Account:
    id: UUID
    user_id: UUID
    connection_id: UUID
    provider_account_id: str
    type: AccountType
    name: str
    currency: str
    balance: Decimal
    balance_updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConsolidatedBalance:
    """Resultado de RN-02. ``total`` é o saldo disponível (contas de depósito +
    reservas de liquidez, ex.: Rende Fácil); ``cash`` é só o saldo em conta;
    ``reserves`` as reservas de liquidez; ``investments`` a soma dos
    investimentos de prazo (CDB, fundos), reportada À PARTE — não entra no
    total; ``credit_card`` (passivo) também à parte."""

    total: Decimal
    cash: Decimal
    reserves: Decimal
    investments: Decimal
    credit_card: Decimal
    by_type: dict[AccountType, Decimal]


def consolidated_balance(
    accounts: Iterable[Account],
    *,
    reserves_total: Decimal = Decimal("0"),
    investments_total: Decimal = Decimal("0"),
) -> ConsolidatedBalance:
    """RN-02: o saldo (``total``) soma as contas de depósito e as reservas de
    liquidez (Rende Fácil). Investimentos de prazo (CDB, fundos) e cartão de
    crédito ficam à parte, fora do total. O chamador passa apenas contas ativas."""
    cash = Decimal("0")
    credit_card = Decimal("0")
    by_type: dict[AccountType, Decimal] = {}
    for account in accounts:
        by_type[account.type] = by_type.get(account.type, Decimal("0")) + account.balance
        if account.type == AccountType.CREDIT_CARD:
            credit_card += account.balance
        else:
            cash += account.balance
    return ConsolidatedBalance(
        total=cash + reserves_total,
        cash=cash,
        reserves=reserves_total,
        investments=investments_total,
        credit_card=credit_card,
        by_type=by_type,
    )
