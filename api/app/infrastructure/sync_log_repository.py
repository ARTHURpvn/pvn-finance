"""Adapter SQLAlchemy do repositório de sync_logs (NFR-009)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.models import SyncLogModel


class SqlSyncLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def start(self, connection_id: UUID) -> UUID:
        model = SyncLogModel(connection_id=connection_id, status="running")
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return model.id

    def finish(self, log_id: UUID, *, status: str, error: str | None = None) -> None:
        model = self._session.get(SyncLogModel, log_id)
        if model is not None:
            model.status = status
            model.error = error
            model.finished_at = datetime.now(UTC)
            self._session.commit()
