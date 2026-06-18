"""Rotas de transações (F6) — listagem paginada e filtrada (FR-010/013).

Nunca expõe ``raw`` nem segredos."""

from datetime import date as date_type
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import api_error
from app.api.schemas import (
    RecategorizeRequest,
    TransactionResponse,
    TransactionsPage,
)
from app.domain.rule import MatchType
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.rule_repository import SqlRuleRepository
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


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def recategorize(
    transaction_id: UUID,
    body: RecategorizeRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> TransactionResponse:
    """FR-017 / RN-04: altera SOMENTE a categoria; opcionalmente cria regra."""
    tx_repo = SqlTransactionRepository(session)
    transaction = tx_repo.get(transaction_id, current_user.id)
    if transaction is None:
        raise api_error(
            code="transaction_not_found",
            message="Transação não encontrada",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    category = SqlCategoryRepository(session).get_for_user(
        body.category_id, current_user.id
    )
    if category is None:
        raise api_error(
            code="category_not_found",
            message="Categoria inválida",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    tx_repo.set_category(transaction_id, current_user.id, body.category_id)

    if body.create_rule:
        SqlRuleRepository(session).add(
            user_id=current_user.id,
            match_type=MatchType.CONTAINS,
            pattern=transaction.description,
            category_id=body.category_id,
            priority=10,
        )

    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        date=transaction.date,
        amount=str(transaction.amount),
        direction=transaction.direction.value,
        description=transaction.description,
        counterpart=transaction.counterpart,
        category_id=body.category_id,
        category_name=category.name,
    )
