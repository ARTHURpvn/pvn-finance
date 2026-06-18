"""RN-02 — saldo consolidado exclui cartão de crédito do total positivo."""

from decimal import Decimal
from uuid import uuid4

from app.domain.account import Account, AccountType, consolidated_balance


def _acc(type_: AccountType, balance: str) -> Account:
    return Account(
        id=uuid4(),
        user_id=uuid4(),
        connection_id=uuid4(),
        provider_account_id="pa",
        type=type_,
        name=type_.value,
        currency="BRL",
        balance=Decimal(balance),
    )


def test_credit_card_excluded_from_total() -> None:
    accounts = [
        _acc(AccountType.CHECKING, "1000.00"),
        _acc(AccountType.SAVINGS, "500.00"),
        _acc(AccountType.CREDIT_CARD, "-300.00"),
    ]

    result = consolidated_balance(accounts)

    assert result.total == Decimal("1500.00")  # cartão fora
    assert result.credit_card == Decimal("-300.00")
    assert result.by_type[AccountType.CREDIT_CARD] == Decimal("-300.00")
    assert result.by_type[AccountType.CHECKING] == Decimal("1000.00")


def test_empty_accounts_returns_zero() -> None:
    result = consolidated_balance([])
    assert result.total == Decimal("0")
    assert result.credit_card == Decimal("0")
    assert result.by_type == {}


def test_multiple_accounts_same_type_are_summed() -> None:
    accounts = [
        _acc(AccountType.CHECKING, "100"),
        _acc(AccountType.CHECKING, "250"),
    ]
    result = consolidated_balance(accounts)
    assert result.by_type[AccountType.CHECKING] == Decimal("350")
    assert result.total == Decimal("350")
