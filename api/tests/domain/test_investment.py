"""Investimentos no patrimônio + flag de movimentação (is_transfer)."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.account import Account, AccountType, consolidated_balance
from app.domain.investment import (
    Investment,
    is_liquid_reserve,
    total_invested,
    total_reserves,
)
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


def _investment(
    balance: str,
    name: str = "CDB - NU FINANCEIRA",
    subtype: str | None = None,
) -> Investment:
    return Investment(
        id=uuid4(),
        user_id=uuid4(),
        connection_id=uuid4(),
        provider_investment_id="i",
        name=name,
        type="FIXED_INCOME",
        balance=Decimal(balance),
        subtype=subtype,
    )


def test_is_liquid_reserve() -> None:
    # Só poupança de verdade (subtype SAVINGS) é reserva/saldo.
    assert is_liquid_reserve(_investment("1", "Poupança", subtype="SAVINGS"))
    # A caixinha Rende Fácil é fundo de investimento → NÃO é reserva.
    assert not is_liquid_reserve(
        _investment("1", "BB Renda Fixa Simples Reserva", subtype="INVESTMENT_FUND")
    )
    assert not is_liquid_reserve(_investment("1", "BB Rende Fácil"))
    assert not is_liquid_reserve(_investment("1", "CDB - NU FINANCEIRA"))


def test_total_invested_excludes_reserves() -> None:
    invs = [
        _investment("100.00", "CDB - NU FINANCEIRA"),  # prazo
        _investment("50.50", "Poupança", subtype="SAVINGS"),  # reserva (não conta)
    ]
    assert total_invested(invs) == Decimal("100.00")
    assert total_reserves(invs) == Decimal("50.50")


def test_patrimonio_reserva_no_saldo_investimento_a_parte() -> None:
    accounts = [
        _account(AccountType.CHECKING, "774.81"),
        _account(AccountType.CREDIT_CARD, "1956.00"),
    ]
    bal = consolidated_balance(
        accounts,
        reserves_total=Decimal("1000.00"),  # Rende Fácil → conta no total
        investments_total=Decimal("1175.44"),  # CDB → à parte
    )

    assert bal.cash == Decimal("774.81")
    assert bal.reserves == Decimal("1000.00")
    assert bal.investments == Decimal("1175.44")  # fora do total
    assert bal.credit_card == Decimal("1956.00")  # à parte (passivo)
    assert bal.total == Decimal("1774.81")  # cash 774.81 + reserva 1000


@pytest.mark.parametrize(
    "category,expected",
    [
        ("Automatic investment", True),
        ("Investments", True),
        ("Proceeds interests and dividends", True),
        ("Same person transfer", True),  # transferência entre contas próprias
        ("AUTOMATIC INVESTMENT", True),  # case-insensitive
        ("Food", False),
        ("Transfer - PIX", False),  # PIX a terceiros continua sendo gasto
        ("Credit card payment", False),  # pagamento de fatura = gasto (caixa)
        (None, False),
    ],
)
def test_is_flow_neutral(category: str | None, expected: bool) -> None:
    assert is_flow_neutral(category) is expected
