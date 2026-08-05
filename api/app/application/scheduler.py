"""Varredura de sincronização agendada (F9 / FR-023).

Sincroniza todas as conexões ativas "devidas" (sem sync ou sync antigo),
reaproveitando o SyncService (que já trata backoff e sync_logs)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.application.sync_service import SyncFailed
from app.bootstrap import build_sync_service, make_user_adapter
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.logging_config import get_logger

logger = get_logger("consolida.scheduler")


@dataclass(frozen=True, slots=True)
class SweepResult:
    total: int
    succeeded: int
    failed: int


def sync_due_connections(
    *,
    session: Session,
    now: datetime | None = None,
    stale_minutes: int = 60,
) -> SweepResult:
    now = now or datetime.now(UTC)
    threshold = now - timedelta(minutes=stale_minutes)
    connections = SqlConnectionRepository(session).list_due(threshold)

    succeeded = 0
    failed = 0
    logger.info("sweep.start due=%d", len(connections))
    for connection in connections:
        # Cada conexão sincroniza com as credenciais Pluggy do próprio dono.
        adapter = make_user_adapter(session, connection.user_id)
        if adapter is None:
            logger.warning(
                "sweep.skip connection_id=%s reason=no_credentials", connection.id
            )
            continue
        sync = build_sync_service(session, adapter)
        try:
            result = sync.sync(connection_id=connection.id, user_id=connection.user_id)
            succeeded += 1
            logger.info(
                "sweep.synced connection_id=%s status=%s imported=%d",
                connection.id,
                result.status,
                result.imported,
            )
        except SyncFailed:
            failed += 1
            logger.warning("sweep.failed connection_id=%s", connection.id)

    logger.info("sweep.done total=%d ok=%d failed=%d", len(connections), succeeded, failed)
    return SweepResult(total=len(connections), succeeded=succeeded, failed=failed)
