"""Investimentos no patrimônio + flag de movimentação (is_transfer)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.account import Account, AccountType, consolidated_balance
from app.domain.investment import Investment, total_invested
from app.domain.transaction import is_flow_neutral


def _account(type_: AccountType, balance: str) -> Account:
    return Account(
        id=uuid4(),
        user_id=uuid4(),
        connection_id=uuid4(),
        provider_account_id="p",
        type=type_,
        name="c",
        currency="BRL",
        balance=Decimal(balance),
    )


def _investment(balance: str) -> Investment:
    return Investment(
        id=uuid4(),
        user_id=uuid4(),
        connection_id=uuid4(),
        provider_investment_id="i",
        name="BB Rende Fácil",
        type="MUTUAL_FUND",
        balance=Decimal(balance),
    )


def test_total_invested_sums_balances() -> None:
    assert total_invested([_investment("100.00"), _investment("50.50")]) == Decimal(
        "150.50"
    )


def test_total_invested_empty_is_zero() -> None:
    assert total_invested([]) == Decimal("0")


def test_patrimonio_inclui_investimentos_e_exclui_cartao() -> None:
    accounts = [
        _account(AccountType.CHECKING, "774.81"),
        _account(AccountType.CREDIT_CARD, "1956.00"),
    ]
    bal = consolidated_balance(accounts, investments_total=Decimal("1175.44"))

    assert bal.cash == Decimal("774.81")
    assert bal.investments == Decimal("1175.44")
    assert bal.credit_card == Decimal("1956.00")  # à parte (passivo)
    assert bal.total == Decimal("1950.25")  # 774.81 + 1175.44 (sem cartão)


@pytest.mark.parametrize(
    "category,expected",
    [
        ("Automatic investment", True),
        ("Investments", True),
        ("Proceeds interests and dividends", True),
        ("Same person transfer", True),  # transferência entre contas próprias
        ("Credit card payment", True),  # pagamento de fatura (evita duplicar)
        ("AUTOMATIC INVESTMENT", True),  # case-insensitive
        ("Food", False),
        ("Transfer - PIX", False),  # PIX a terceiros continua sendo gasto
        (None, False),
    ],
)
def test_is_flow_neutral(category: str | None, expected: bool) -> None:
    assert is_flow_neutral(category) is expected
