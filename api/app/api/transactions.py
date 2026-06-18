"""Rotas de transações (F6) — listagem paginada e filtrada (FR-010/013).

Nunca expõe ``raw`` nem segredos."""

from datetime import date as date_type
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.schemas import TransactionResponse, TransactionsPage
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.transaction_repository import SqlTransactionRepository

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionsPage)
def list_transactions(
    current_user: CurrentUser,
    session: SessionDep,
    account_id: UUID | None = None,
    from_: Annotated[date_type | None, Query(alias="from")] = None,
    to: date_type | None = None,
    category_id: UUID | None = None,
    q: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> TransactionsPage:
    items, total = SqlTransactionRepository(session).search(
        user_id=current_user.id,
        account_id=account_id,
        date_from=from_,
        date_to=to,
        category_id=category_id,
        query=q,
        page=page,
        page_size=page_size,
    )

    categories = {
        c.id: c.name for c in SqlCategoryRepository(session).list_for_user(current_user.id)
    }

    return TransactionsPage(
        items=[
            TransactionResponse(
                id=t.id,
                account_id=t.account_id,
                date=t.date,
                amount=str(t.amount),
                direction=t.direction.value,
                description=t.description,
                counterpart=t.counterpart,
                category_id=t.category_id,
                category_name=categories.get(t.category_id) if t.category_id else None,
            )
            for t in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )
