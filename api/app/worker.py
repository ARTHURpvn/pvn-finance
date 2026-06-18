"""Worker de sync agendado (F9 / FR-023).

Executa varreduras periódicas sincronizando conexões devidas. Rodar com:
``python -m app.worker``."""

import time
from datetime import UTC, datetime

from app.application.scheduler import sync_due_connections
from app.bootstrap import make_financial_adapter
from app.config import get_settings
from app.infrastructure.db import get_sessionmaker
from app.logging_config import get_logger, setup_logging

logger = get_logger("consolida.worker")


def run_once() -> None:
    settings = get_settings()
    adapter = make_financial_adapter()
    if adapter is None:
        logger.warning("worker.skip reason=adapter_unconfigured")
        return
    with get_sessionmaker()() as session:
        sync_due_connections(
            session=session,
            adapter=adapter,
            now=datetime.now(UTC),
            stale_minutes=settings.sync_stale_minutes,
        )


def main() -> None:  # pragma: no cover - loop de processo
    setup_logging()
    interval = get_settings().sync_interval_minutes * 60
    logger.info("worker.start interval_s=%d", interval)
    while True:
        try:
            run_once()
        except Exception:  # noqa: BLE001 - worker não pode morrer numa varredura
            logger.exception("worker.sweep_error")
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover
    main()
