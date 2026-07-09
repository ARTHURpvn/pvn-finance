"""Rotas de contas (F6) — listagem com saldo + consolidado (RN-02)."""

from decimal import Decimal

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.api.schemas import (
    AccountResponse,
    AccountsResponse,
    AccountSummary,
    InvestmentResponse,
)
from app.domain.account import consolidated_balance
from app.domain.investment import total_invested
from app.infrastructure.account_repository import SqlAccountRepository
from app.infrastructure.investment_repository import SqlInvestmentRepository

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=AccountsResponse)
def list_accounts(current_user: CurrentUser, session: SessionDep) -> AccountsResponse:
    accounts = SqlAccountRepository(session).list_by_user(current_user.id)
    investments = SqlInvestmentRepository(session).list_by_user(current_user.id)
    balance = consolidated_balance(
        accounts, investments_total=total_invested(investments)
    )
    return AccountsResponse(
        accounts=[
            AccountResponse(
                id=a.id,
                connection_id=a.connection_id,
                type=a.type.value,
                name=a.name,
                currency=a.currency,
                balance=str(a.balance),
                balance_updated_at=a.balance_updated_at,
            )
            for a in accounts
        ],
        investments=[
            InvestmentResponse(
                name=i.name, type=i.type, balance=str(i.balance)
            )
            for i in investments
        ],
        summary=AccountSummary(
            total=str(balance.total or Decimal("0")),
            cash=str(balance.cash or Decimal("0")),
            investments=str(balance.investments or Decimal("0")),
            credit_card=str(balance.credit_card or Decimal("0")),
        ),
    )
