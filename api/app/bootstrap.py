"""Composição (wiring) reutilizável fora do ciclo de request — usado pelo
webhook e pelo worker, além das dependências da API."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.adapters.pluggy import PluggyAdapter
from app.application.categorization_service import CategorizationService
from app.application.sync_service import SyncService
from app.config import get_settings
from app.infrastructure.account_repository import SqlAccountRepository
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.investment_repository import SqlInvestmentRepository
from app.infrastructure.pluggy_credential_repository import (
    SqlPluggyCredentialRepository,
)
from app.infrastructure.rule_repository import SqlRuleRepository
from app.infrastructure.sync_log_repository import SqlSyncLogRepository
from app.infrastructure.transaction_repository import SqlTransactionRepository
from app.infrastructure.vault import CredentialVault
from app.ports.financial_data_port import FinancialDataPort


def get_vault() -> CredentialVault:
    return CredentialVault(get_settings().vault_key)


def make_user_adapter(session: Session, user_id: UUID) -> FinancialDataPort | None:
    """Constrói o adapter do agregador com as credenciais Pluggy DO USUÁRIO
    (multi-tenant). None se o usuário ainda não configurou nas Configurações.
    Não usa mais credenciais do ambiente."""
    creds = SqlPluggyCredentialRepository(session, get_vault()).get(user_id)
    if creds is None:
        return None
    return PluggyAdapter(
        client_id=creds.client_id,
        client_secret=creds.client_secret,
        base_url=creds.base_url,
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
        investments=SqlInvestmentRepository(session),
    )
