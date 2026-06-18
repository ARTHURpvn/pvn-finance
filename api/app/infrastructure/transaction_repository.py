"""Adapter SQLAlchemy do repositório de transações."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.transaction import Transaction
from app.infrastructure.models import TransactionModel


class SqlTransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

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
