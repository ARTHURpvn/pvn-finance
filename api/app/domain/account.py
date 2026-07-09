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
    """Resultado de RN-02. ``total`` é o patrimônio (contas de depósito +
    investimentos); ``cash`` é só o saldo em conta; ``investments`` a soma dos
    investimentos; ``credit_card`` (passivo) fica à parte. ``by_type`` detalha
    as contas."""

    total: Decimal
    cash: Decimal
    investments: Decimal
    credit_card: Decimal
    by_type: dict[AccountType, Decimal]


def consolidated_balance(
    accounts: Iterable[Account], *, investments_total: Decimal = Decimal("0")
) -> ConsolidatedBalance:
    """RN-02: soma os saldos das contas de depósito e os investimentos no
    patrimônio; cartão de crédito NÃO entra no total (é passivo, reportado à
    parte). O chamador deve passar apenas contas ativas."""
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
        total=cash + investments_total,
        cash=cash,
        investments=investments_total,
        credit_card=credit_card,
        by_type=by_type,
    )
