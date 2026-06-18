"""Adapter SQLAlchemy do repositório de conexões (escopado por user_id)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.connection import Connection, ConnectionStatus
from app.infrastructure.models import ConnectionModel


class SqlConnectionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: ConnectionModel) -> Connection:
        return Connection(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,
            provider_item_id=model.provider_item_id,
            institution_name=model.institution_name,
            status=ConnectionStatus(model.status),
            consent_expires_at=model.consent_expires_at,
            last_sync_at=model.last_sync_at,
        )

    def add(
        self,
        *,
        user_id: UUID,
        provider: str,
        provider_item_id: str,
        institution_name: str,
        status: ConnectionStatus = ConnectionStatus.ATIVA,
        encrypted_secret: bytes | None = None,
        consent_expires_at: datetime | None = None,
    ) -> Connection:
        model = ConnectionModel(
            user_id=user_id,
            provider=provider,
            provider_item_id=provider_item_id,
            institution_name=institution_name,
            status=status.value,
            encrypted_secret=encrypted_secret,
            consent_expires_at=consent_expires_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def get(self, connection_id: UUID, user_id: UUID) -> Connection | None:
        model = self._session.get(ConnectionModel, connection_id)
        if model is None or model.user_id != user_id:
            return None
        return self._to_domain(model)

    def get_by_provider_item(
        self, provider: str, provider_item_id: str
    ) -> Connection | None:
        stmt = select(ConnectionModel).where(
            ConnectionModel.provider == provider,
            ConnectionModel.provider_item_id == provider_item_id,
        )
        model = self._session.scalar(stmt)
        return self._to_domain(model) if model else None

    def list(self, user_id: UUID) -> list[Connection]:
        stmt = (
            select(ConnectionModel)
            .where(ConnectionModel.user_id == user_id)
            .order_by(ConnectionModel.created_at)
        )
        return [self._to_domain(m) for m in self._session.scalars(stmt)]

    def set_status(self, connection_id: UUID, status: ConnectionStatus) -> None:
        model = self._session.get(ConnectionModel, connection_id)
        if model is not None:
            model.status = status.value
            self._session.commit()

    def mark_synced(
        self,
        connection_id: UUID,
        when: datetime,
        *,
        status: ConnectionStatus = ConnectionStatus.ATIVA,
    ) -> None:
        model = self._session.get(ConnectionModel, connection_id)
        if model is not None:
            model.last_sync_at = when
            model.status = status.value
            self._session.commit()

    def delete(self, connection_id: UUID, user_id: UUID) -> bool:
        """Remove a conexão e, por cascata no banco, todos os dados associados
        (accounts, transactions, sync_logs) — FR-006."""
        model = self._session.get(ConnectionModel, connection_id)
        if model is None or model.user_id != user_id:
            return False
        self._session.delete(model)
        self._session.commit()
        return True
