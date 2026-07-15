"""Investimento — entidade de domínio. Compõe o patrimônio total."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


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
    # Detalhe (renda fixa mensal, ganho/perda, evolução, banco).
    amount_original: Decimal | None = None
    amount_profit: Decimal | None = None
    value: Decimal | None = None
    quantity: Decimal | None = None
    rate: Decimal | None = None
    rate_type: str | None = None
    annual_rate: Decimal | None = None
    last_month_rate: Decimal | None = None
    last_twelve_months_rate: Decimal | None = None
    due_date: date_type | None = None
    purchase_date: date_type | None = None
    institution: str | None = None


def is_fixed_income(investment: Investment) -> bool:
    """Renda fixa (CDB, LCI, LCA, Tesouro, debênture): tem taxa contratada e
    rende de forma previsível — base da 'renda fixa mensal'."""
    return investment.type.upper() == "FIXED_INCOME"


def profit(investment: Investment) -> Decimal | None:
    """Ganho/perda da posição: usa ``amount_profit`` do agregador; senão deriva
    de (atual − aplicado). None quando não há como saber."""
    if investment.amount_profit is not None:
        return investment.amount_profit
    if investment.amount_original is not None:
        return investment.balance - investment.amount_original
    return None


def total_profit(investments: Iterable[Investment]) -> Decimal:
    """Soma o ganho/perda das posições que têm essa informação."""
    return sum((p for i in investments if (p := profit(i)) is not None), _ZERO)


def effective_annual_rate(
    investment: Investment, cdi_annual_pct: Decimal
) -> Decimal | None:
    """Taxa anual efetiva (%) da posição, para estimar a renda mensal.

    Precedência: ``annual_rate`` (o agregador já dá a rentabilidade anual) →
    taxa contratada (``rate`` + ``rate_type``): CDI ⇒ ``rate% × CDI``; PRE/
    prefixado ⇒ o próprio ``rate``. Retorna None quando não dá para estimar."""
    if investment.annual_rate is not None:
        return investment.annual_rate
    if investment.rate is None:
        return None
    kind = (investment.rate_type or "").upper()
    if kind == "CDI":
        return investment.rate / _HUNDRED * cdi_annual_pct
    if kind in ("PRE", "PREFIXADO", "PREFIXED", ""):
        return investment.rate
    # IPCA e outros indexadores: sem o índice não estimamos.
    return None


def is_variable_income(investment: Investment) -> bool:
    """Renda variável que paga mensalmente (FIIs, ações): é o que retorna
    dinheiro no bolso todo mês (dividendos/proventos)."""
    return investment.type.upper() in ("EQUITY", "ETF") or (
        investment.subtype or ""
    ).upper() == "REAL_ESTATE_FUND"


def monthly_income(investment: Investment, fii_monthly_yield: Decimal) -> Decimal:
    """Renda mensal estimada (R$) da posição que paga mensal (FII/ação):
    saldo × dividend yield mensal. O Pluggy não entrega o provento, então é
    estimativa. Zero para o que não paga mensal (ex.: CDB, que vence no prazo)."""
    if not is_variable_income(investment):
        return _ZERO
    return investment.balance * fii_monthly_yield / _HUNDRED


def total_monthly_income(
    investments: Iterable[Investment], fii_monthly_yield: Decimal
) -> Decimal:
    """Renda mensal estimada somando as posições que pagam mensal (FIIs/ações)."""
    return sum((monthly_income(i, fii_monthly_yield) for i in investments), _ZERO)


def _month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def _value_at(investment: Investment, month_idx: int, now_idx: int) -> Decimal:
    """Valor estimado da posição no fim do mês ``month_idx``.

    O Pluggy não entrega histórico, então interpolamos linearmente entre o
    valor aplicado (na compra) e o valor atual (hoje). Sem data de compra ou
    valor aplicado, assumimos o saldo atual constante no período exibido."""
    p, o, b = investment.purchase_date, investment.amount_original, investment.balance
    if p is None or o is None:
        return b
    buy_idx = _month_index(p.year, p.month)
    if month_idx < buy_idx:
        return _ZERO
    if month_idx >= now_idx or now_idx == buy_idx:
        return b
    frac = Decimal(month_idx - buy_idx) / Decimal(now_idx - buy_idx)
    return o + (b - o) * frac


@dataclass(frozen=True, slots=True)
class EvolutionPoint:
    month: str  # "YYYY-MM"
    total: Decimal


def monthly_evolution(
    investments: Iterable[Investment], today: date_type, months: int = 12
) -> list[EvolutionPoint]:
    """Evolução do total investido nos últimos ``months`` meses (inclui o atual).
    Estimativa (interpolação aplicado→atual por posição)."""
    invs = list(investments)
    now_idx = _month_index(today.year, today.month)
    points: list[EvolutionPoint] = []
    for offset in range(months - 1, -1, -1):
        idx = now_idx - offset
        year, month = divmod(idx, 12)
        total = sum((_value_at(i, idx, now_idx) for i in invs), _ZERO)
        points.append(EvolutionPoint(month=f"{year:04d}-{month + 1:02d}", total=total))
    return points


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
