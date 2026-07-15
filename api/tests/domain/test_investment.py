"""Investimentos no patrimônio + flag de movimentação (is_transfer)."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.account import Account, AccountType, consolidated_balance
from app.domain.investment import (
    Investment,
    effective_annual_rate,
    is_fixed_income,
    is_liquid_reserve,
    monthly_evolution,
    monthly_income,
    profit,
    total_invested,
    total_monthly_income,
    total_profit,
    total_reserves,
)
from app.domain.transaction import is_flow_neutral

_CDI = Decimal("10")  # CDI anual (%) de teste, fácil de conferir na mão


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


def _fixed(
    balance: str,
    *,
    amount_original: str | None = None,
    rate: str | None = None,
    rate_type: str | None = None,
    annual_rate: str | None = None,
    purchase: date | None = None,
    type_: str = "FIXED_INCOME",
) -> Investment:
    return Investment(
        id=uuid4(),
        user_id=uuid4(),
        connection_id=uuid4(),
        provider_investment_id="i",
        name="CDB",
        type=type_,
        balance=Decimal(balance),
        amount_original=Decimal(amount_original) if amount_original else None,
        rate=Decimal(rate) if rate else None,
        rate_type=rate_type,
        annual_rate=Decimal(annual_rate) if annual_rate else None,
        purchase_date=purchase,
    )


def test_effective_annual_rate_cdi() -> None:
    # CDB a 115% do CDI, CDI 10% → 11,5% a.a.
    inv = _fixed("1000", rate="115", rate_type="CDI")
    assert effective_annual_rate(inv, _CDI) == Decimal("11.5")


def test_effective_annual_rate_prefers_annual_rate() -> None:
    inv = _fixed("1000", rate="115", rate_type="CDI", annual_rate="9")
    assert effective_annual_rate(inv, _CDI) == Decimal("9")


def test_monthly_income_fixed_income() -> None:
    # 1000 × 12% a.a. / 12 = 10/mês
    inv = _fixed("1000", annual_rate="12")
    assert monthly_income(inv, _CDI) == Decimal("10")


def test_monthly_income_zero_when_not_fixed_income() -> None:
    inv = _fixed("1000", annual_rate="12", type_="EQUITY")
    assert not is_fixed_income(inv)
    assert monthly_income(inv, _CDI) == Decimal("0")


def test_profit_from_original_and_total() -> None:
    a = _fixed("1100", amount_original="1000")
    b = _fixed("500", amount_original="520")  # prejuízo
    assert profit(a) == Decimal("100")
    assert profit(b) == Decimal("-20")
    assert total_profit([a, b]) == Decimal("80")


def test_total_monthly_income_sums_fixed_income() -> None:
    a = _fixed("1000", annual_rate="12")  # 10/mês
    b = _fixed("2000", annual_rate="6")   # 10/mês
    assert total_monthly_income([a, b], _CDI) == Decimal("20")


def test_monthly_evolution_interpolates_and_labels_months() -> None:
    # comprado em maio a 900, hoje (julho) vale 960 → junho ≈ 930
    inv = _fixed("960", amount_original="900", purchase=date(2026, 5, 1))
    pts = monthly_evolution([inv], today=date(2026, 7, 15), months=4)
    months = [p.month for p in pts]
    assert months == ["2026-04", "2026-05", "2026-06", "2026-07"]
    by = {p.month: p.total for p in pts}
    assert by["2026-04"] == Decimal("0")       # antes da compra
    assert by["2026-05"] == Decimal("900")     # aplicado
    assert by["2026-07"] == Decimal("960")     # atual
    assert by["2026-06"] == Decimal("930")     # metade do caminho
