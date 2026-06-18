"""Adapter SQLAlchemy do repositório de transações."""

from datetime import date as date_type
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.transaction import Direction, Transaction
from app.infrastructure.models import TransactionModel


class SqlTransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            account_id=model.account_id,
            provider_transaction_id=model.provider_transaction_id,
            date=model.date,
            amount=model.amount,
            direction=Direction(model.direction),
            description=model.description,
            counterpart=model.counterpart,
            category_id=model.category_id,
        )

    def search(
        self,
        *,
        user_id: UUID,
        account_id: UUID | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        category_id: UUID | None = None,
        query: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Transaction], int]:
        """Lista transações do usuário com filtros e paginação (FR-010/013).
        Retorna (itens da página, total de resultados)."""
        conditions = [TransactionModel.user_id == user_id]
        if account_id is not None:
            conditions.append(TransactionModel.account_id == account_id)
        if date_from is not None:
            conditions.append(TransactionModel.date >= date_from)
        if date_to is not None:
            conditions.append(TransactionModel.date <= date_to)
        if category_id is not None:
            conditions.append(TransactionModel.category_id == category_id)
        if query:
            conditions.append(TransactionModel.description.ilike(f"%{query}%"))

        total = self._session.scalar(
            select(func.count()).select_from(TransactionModel).where(*conditions)
        )
        stmt = (
            select(TransactionModel)
            .where(*conditions)
            .order_by(TransactionModel.date.desc(), TransactionModel.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        items = [self._to_domain(m) for m in self._session.scalars(stmt)]
        return items, int(total or 0)

    def existing_provider_ids(self, connection_id: UUID) -> set[str]:
        """Ids de transações já persistidas na conexão (base do dedupe RN-05)."""
        stmt = select(TransactionModel.provider_transaction_id).where(
            TransactionModel.connection_id == connection_id
        )
        return set(self._session.scalars(stmt))

    def add_many(
        self,
        connection_id: UUID,
        items: list[tuple[Transaction, dict[str, Any] | None]],
    ) -> int:
        """Persiste transações novas. Commit atômico (chamado por conta)."""
        models = [
            TransactionModel(
                id=tx.id,
                user_id=tx.user_id,
                account_id=tx.account_id,
                connection_id=connection_id,
                provider_transaction_id=tx.provider_transaction_id,
                date=tx.date,
                amount=tx.amount,
                direction=tx.direction.value,
                description=tx.description,
                counterpart=tx.counterpart,
                category_id=tx.category_id,
                raw=raw,
            )
            for tx, raw in items
        ]
        if not models:
            return 0
        self._session.add_all(models)
        self._session.commit()
        return len(models)
