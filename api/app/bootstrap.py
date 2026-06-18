"""Composição (wiring) reutilizável fora do ciclo de request — usado pelo
webhook e pelo worker, além das dependências da API."""

from sqlalchemy.orm import Session

from app.adapters.pluggy import PluggyAdapter
from app.application.categorization_service import CategorizationService
from app.application.sync_service import SyncService
from app.config import get_settings
from app.infrastructure.account_repository import SqlAccountRepository
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.rule_repository import SqlRuleRepository
from app.infrastructure.sync_log_repository import SqlSyncLogRepository
from app.infrastructure.transaction_repository import SqlTransactionRepository
from app.ports.financial_data_port import FinancialDataPort


def make_financial_adapter() -> FinancialDataPort | None:
    """Constrói o adapter do agregador a partir do ambiente; None se não
    configurado (sem credenciais)."""
    settings = get_settings()
    if not settings.pluggy_client_id or not settings.pluggy_client_secret:
        return None
    return PluggyAdapter(
        client_id=settings.pluggy_client_id,
        client_secret=settings.pluggy_client_secret,
        base_url=settings.pluggy_base_url,
    )


def build_sync_service(session: Session, adapter: FinancialDataPort) -> SyncService:
    return SyncService(
        adapter=adapter,
        connections=SqlConnectionRepository(session),
        accounts=SqlAccountRepository(session),
        transactions=SqlTransactionRepository(session),
        sync_logs=SqlSyncLogRepository(session),
        categorization=CategorizationService(
            categories=SqlCategoryRepository(session),
            rules=SqlRuleRepository(session),
        ),
    )
