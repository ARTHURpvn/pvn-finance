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
    """Resultado de RN-02. ``total`` exclui cartão de crédito (passivo);
    ``credit_card`` é reportado à parte. ``by_type`` traz o detalhamento."""

    total: Decimal
    credit_card: Decimal
    by_type: dict[AccountType, Decimal]


def consolidated_balance(accounts: Iterable[Account]) -> ConsolidatedBalance:
    """RN-02: soma os saldos das contas informadas; cartão de crédito NÃO
    entra no total positivo (é passivo). O chamador deve passar apenas
    contas ativas."""
    total = Decimal("0")
    credit_card = Decimal("0")
    by_type: dict[AccountType, Decimal] = {}
    for account in accounts:
        by_type[account.type] = by_type.get(account.type, Decimal("0")) + account.balance
        if account.type == AccountType.CREDIT_CARD:
            credit_card += account.balance
        else:
            total += account.balance
    return ConsolidatedBalance(total=total, credit_card=credit_card, by_type=by_type)
