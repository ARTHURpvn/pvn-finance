"""Rotas do dashboard (F8) — agregações por período (FR-018/019/020)."""

from datetime import date as date_type
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ApiRateLimit, CurrentUser, SessionDep
from app.api.schemas import (
    CategorySpendResponse,
    DashboardSummary,
    TimelinePointResponse,
)
from app.infrastructure.dashboard_repository import SqlDashboardRepository

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[ApiRateLimit]
)

DateFrom = Annotated[date_type | None, Query(alias="from")]


@router.get("/summary", response_model=DashboardSummary)
def summary(
    current_user: CurrentUser,
    session: SessionDep,
    from_: DateFrom = None,
    to: date_type | None = None,
) -> DashboardSummary:
    s = SqlDashboardRepository(session).summary(current_user.id, from_, to)
    return DashboardSummary(
        received=str(s.received), spent=str(s.spent), net=str(s.net)
    )


@router.get("/by-account")
def by_account(
    current_user: CurrentUser,
    session: SessionDep,
    from_: DateFrom = None,
    to: date_type | None = None,
) -> list[dict[str, str]]:
    """Líquido (entrou − saiu) por conta no período — usado para o saldo do
    banco = Entrou − Saiu do mês."""
    nets = SqlDashboardRepository(session).net_by_account(current_user.id, from_, to)
    return [
        {"account_id": str(account_id), "net": str(net)}
        for account_id, net in nets.items()
    ]


@router.get("/by-category", response_model=list[CategorySpendResponse])
def by_category(
    current_user: CurrentUser,
    session: SessionDep,
    from_: DateFrom = None,
    to: date_type | None = None,
) -> list[CategorySpendResponse]:
    rows = SqlDashboardRepository(session).by_category(current_user.id, from_, to)
    return [
        CategorySpendResponse(category=r.category, total=str(r.total)) for r in rows
    ]


@router.get("/timeline", response_model=list[TimelinePointResponse])
def timeline(
    current_user: CurrentUser,
    session: SessionDep,
    from_: DateFrom = None,
    to: date_type | None = None,
) -> list[TimelinePointResponse]:
    rows = SqlDashboardRepository(session).timeline(current_user.id, from_, to)
    return [
        TimelinePointResponse(
            month=r.month, inflow=str(r.inflow), outflow=str(r.outflow)
        )
        for r in rows
    ]
