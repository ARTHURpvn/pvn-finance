"""Rotas de investimentos — detalhe por posição, renda fixa mensal estimada,
ganho/perda e evolução mês a mês. Somente leitura."""

from datetime import date as date_type
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import ApiRateLimit, CurrentUser, SessionDep
from app.api.schemas import (
    InvestmentDetailResponse,
    InvestmentEvolutionPoint,
    InvestmentsResponse,
    InvestmentsSummary,
)
from app.config import get_settings
from app.domain.investment import (
    effective_annual_rate,
    is_fixed_income,
    monthly_evolution,
    monthly_income,
    profit,
    total_monthly_income,
    total_profit,
)
from app.infrastructure.investment_repository import SqlInvestmentRepository
from app.infrastructure.models import ConnectionModel

router = APIRouter(
    prefix="/investments", tags=["investments"], dependencies=[ApiRateLimit]
)


def _s(value: object | None) -> str | None:
    return None if value is None else str(value)


_VARIABLE_INCOME = frozenset({"EQUITY", "ETF"})


def _bank_of(
    name: str, type_: str, institution: str | None, conn_institution: str | None
) -> str:
    """Banco/corretora onde o ativo está aplicado. Em produção, cada conexão é
    uma instituição real (ex.: XP) → usa ela direto. No sandbox tudo vem como
    'MeuPluggy', então derivamos do tipo/nome (só para um demo legível)."""
    if conn_institution and conn_institution.strip().lower() != "meupluggy":
        return conn_institution
    # A renda variável (ações/FIIs) do usuário fica toda no XP.
    if type_.upper() in _VARIABLE_INCOME:
        return "XP Investimentos"
    text = f"{name} {institution or ''}".lower()
    if any(k in text for k in ("nu financeira", "nubank", "nu pagamentos")):
        return "Nubank"
    if "banco do brasil" in text or text.startswith("bb "):
        return "Banco do Brasil"
    if "xp" in text:
        return "XP Investimentos"
    return institution or "Outros"


@router.get("", response_model=InvestmentsResponse)
def list_investments(
    current_user: CurrentUser, session: SessionDep
) -> InvestmentsResponse:
    cdi = get_settings().cdi_annual_rate
    invs = [
        i
        for i in SqlInvestmentRepository(session).list_by_user(current_user.id)
        if i.balance > 0  # esconde posições zeradas (resgatadas)
    ]

    # Banco onde está aplicado: instituição da posição ou da conexão.
    conn_bank = dict(
        session.execute(
            select(ConnectionModel.id, ConnectionModel.institution_name).where(
                ConnectionModel.user_id == current_user.id
            )
        ).all()
    )

    items = [
        InvestmentDetailResponse(
            name=i.name,
            type=i.type,
            subtype=i.subtype,
            bank=_bank_of(
                i.name, i.type, i.institution, conn_bank.get(i.connection_id)
            ),
            balance=str(i.balance),
            amount_original=_s(i.amount_original),
            profit=_s(profit(i)),
            is_fixed_income=is_fixed_income(i),
            rate=_s(i.rate),
            rate_type=i.rate_type,
            annual_rate=_s(effective_annual_rate(i, cdi)),
            monthly_income=str(monthly_income(i, cdi)),
            due_date=i.due_date,
            purchase_date=i.purchase_date,
        )
        for i in invs
    ]

    summary = InvestmentsSummary(
        total_invested=str(sum((i.balance for i in invs), Decimal("0"))),
        total_profit=str(total_profit(invs)),
        monthly_income=str(total_monthly_income(invs, cdi)),
        cdi_annual_rate=str(cdi),
    )

    evolution = [
        InvestmentEvolutionPoint(month=p.month, total=str(p.total))
        for p in monthly_evolution(invs, date_type.today())
    ]

    return InvestmentsResponse(
        investments=items, summary=summary, evolution=evolution
    )
