"""Adapter SQLAlchemy do repositório de transações."""

from datetime import date as date_type
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
            is_transfer=model.is_transfer,
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
        exclude_transfers: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Transaction], int]:
        """Lista transações do usuário com filtros e paginação (FR-010/013).
        Retorna (itens da página, total de resultados). ``exclude_transfers``
        esconde as movimentações do próprio dinheiro (investimento/Rende Fácil,
        transferência entre contas próprias, pagamento de fatura)."""
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
        if exclude_transfers:
            conditions.append(TransactionModel.is_transfer.is_(False))

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

    def get(self, transaction_id: UUID, user_id: UUID) -> Transaction | None:
        model = self._session.get(TransactionModel, transaction_id)
        if model is None or model.user_id != user_id:
            return None
        return self._to_domain(model)

    def set_category(
        self, transaction_id: UUID, user_id: UUID, category_id: UUID | None
    ) -> bool:
        """RN-04: recategorização altera SOMENTE category_id."""
        model = self._session.get(TransactionModel, transaction_id)
        if model is None or model.user_id != user_id:
            return False
        model.category_id = category_id
        self._session.commit()
        return True

    def add_many(
        self,
        connection_id: UUID,
        items: list[tuple[Transaction, dict[str, Any] | None]],
    ) -> int:
        """Persiste transações novas de forma atômica e idempotente (RN-05).

        Usa ``INSERT ... ON CONFLICT DO NOTHING`` sobre a unique
        ``(connection_id, provider_transaction_id)``: o banco descarta
        duplicatas de syncs concorrentes sem corrida. Retorna quantas linhas
        foram de fato inseridas."""
        rows = [
            {
                "id": tx.id,
                "user_id": tx.user_id,
                "account_id": tx.account_id,
                "connection_id": connection_id,
                "provider_transaction_id": tx.provider_transaction_id,
                "date": tx.date,
                "amount": tx.amount,
                "direction": tx.direction.value,
                "description": tx.description,
                "counterpart": tx.counterpart,
                "category_id": tx.category_id,
                "is_transfer": tx.is_transfer,
                "raw": raw,
            }
            for tx, raw in items
        ]
        if not rows:
            return 0
        stmt = (
            pg_insert(TransactionModel)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=["connection_id", "provider_transaction_id"]
            )
            .returning(TransactionModel.id)
        )
        # RETURNING só devolve as linhas efetivamente inseridas — as descartadas
        # por conflito não aparecem, dando a contagem exata (independe de rowcount).
        inserted = self._session.execute(stmt).fetchall()
        self._session.commit()
        return len(inserted)
