"""Dependências FastAPI: sessão, serviço de auth e usuário autenticado."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.adapters.pluggy import PluggyAdapter
from app.api.errors import api_error
from app.application.auth_service import AuthService
from app.application.categorization_service import CategorizationService
from app.application.connection_service import ConnectionService
from app.application.sync_service import SyncService
from app.config import get_settings
from app.domain.user import User
from app.infrastructure.account_repository import SqlAccountRepository
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.db import get_session
from app.infrastructure.rule_repository import SqlRuleRepository
from app.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from app.infrastructure.sync_log_repository import SqlSyncLogRepository
from app.infrastructure.transaction_repository import SqlTransactionRepository
from app.infrastructure.user_repository import SqlUserRepository
from app.ports.financial_data_port import FinancialDataPort
from app.ports.security import TokenError

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(
        users=SqlUserRepository(session),
        hasher=Argon2PasswordHasher(),
        tokens=JwtTokenService(),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = api_error(
        code="unauthorized", message="Não autenticado", status_code=401
    )
    if credentials is None:
        raise unauthorized
    tokens = JwtTokenService()
    try:
        payload = tokens.decode(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise unauthorized from exc
    record = SqlUserRepository(session).get_by_id(UUID(payload["sub"]))
    if record is None:
        raise unauthorized
    return record.to_public()


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_financial_adapter() -> FinancialDataPort:
    settings = get_settings()
    if not settings.pluggy_client_id or not settings.pluggy_client_secret:
        raise api_error(
            code="aggregator_not_configured",
            message="Agregador (Pluggy) não configurado",
            status_code=503,
        )
    return PluggyAdapter(
        client_id=settings.pluggy_client_id,
        client_secret=settings.pluggy_client_secret,
        base_url=settings.pluggy_base_url,
    )


AdapterDep = Annotated[FinancialDataPort, Depends(get_financial_adapter)]


def get_connection_service(
    session: SessionDep, adapter: AdapterDep
) -> ConnectionService:
    return ConnectionService(
        adapter=adapter, connections=SqlConnectionRepository(session)
    )


def get_sync_service(session: SessionDep, adapter: AdapterDep) -> SyncService:
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


ConnectionServiceDep = Annotated[ConnectionService, Depends(get_connection_service)]
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
