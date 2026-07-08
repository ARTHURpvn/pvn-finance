"""SyncService — integração com repositórios reais + adapter fake."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.adapters.fake import FakeFinancialDataAdapter
from app.application.sync_service import SyncFailed, SyncService
from app.domain.connection import ConnectionStatus
from app.infrastructure.account_repository import SqlAccountRepository
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.models import SyncLogModel, TransactionModel
from app.infrastructure.sync_log_repository import SqlSyncLogRepository
from app.infrastructure.transaction_repository import SqlTransactionRepository
from app.infrastructure.user_repository import SqlUserRepository
from app.ports.financial_data_port import (
    AggregatorError,
    ProviderAccount,
    ProviderItem,
    ProviderTransaction,
    RetryableAggregatorError,
)


def _make_service(session: Session, adapter, *, base_delay: float = 0.0) -> SyncService:
    return SyncService(
        adapter=adapter,
        connections=SqlConnectionRepository(session),
        accounts=SqlAccountRepository(session),
        transactions=SqlTransactionRepository(session),
        sync_logs=SqlSyncLogRepository(session),
        base_delay=base_delay,
    )


def _seed_connection(
    session: Session, *, email: str, consent_expires_at: datetime | None = None
) -> tuple[UUID, UUID]:
    user = SqlUserRepository(session).add(email=email, password_hash="x")
    conn = SqlConnectionRepository(session).add(
        user_id=user.id,
        provider="pluggy",
        provider_item_id=f"item-{email}",
        institution_name="Banco X",
        consent_expires_at=consent_expires_at,
    )
    return user.id, conn.id


def _fake_with_data() -> FakeFinancialDataAdapter:
    account = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="Conta",
        currency="BRL",
        balance=Decimal("100.00"),
    )
    txs = [
        ProviderTransaction(
            provider_transaction_id="t1",
            date=date(2026, 1, 1),
            amount=Decimal("-10.00"),
            description="Compra",
        ),
        ProviderTransaction(
            provider_transaction_id="t2",
            date=date(2026, 1, 2),
            amount=Decimal("500.00"),
            description="Salário",
        ),
    ]
    return FakeFinancialDataAdapter(accounts=[account], transactions={"acc-1": txs})


def test_sync_imports_accounts_and_transactions(db_session: Session) -> None:
    user_id, conn_id = _seed_connection(db_session, email="sync1@e.com")
    service = _make_service(db_session, _fake_with_data())

    result = service.sync(connection_id=conn_id, user_id=user_id)

    assert result.status == "ativa"
    assert result.imported == 2
    count = db_session.query(TransactionModel).filter_by(connection_id=conn_id).count()
    assert count == 2


def test_sync_is_idempotent_dedupe(db_session: Session) -> None:
    user_id, conn_id = _seed_connection(db_session, email="sync2@e.com")
    service = _make_service(db_session, _fake_with_data())

    service.sync(connection_id=conn_id, user_id=user_id)
    second = service.sync(connection_id=conn_id, user_id=user_id)

    assert second.imported == 0  # RN-05: nada novo
    count = db_session.query(TransactionModel).filter_by(connection_id=conn_id).count()
    assert count == 2


def test_sync_skips_when_consent_expired(db_session: Session) -> None:
    user_id, conn_id = _seed_connection(
        db_session,
        email="sync3@e.com",
        consent_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    service = _make_service(db_session, _fake_with_data())

    result = service.sync(connection_id=conn_id, user_id=user_id)

    assert result.status == ConnectionStatus.REQUER_REAUTH.value
    assert result.imported == 0
    conn = SqlConnectionRepository(db_session).get(conn_id, user_id)
    assert conn is not None and conn.status == ConnectionStatus.REQUER_REAUTH


def test_sync_marks_reauth_when_item_login_error(db_session: Session) -> None:
    """RN-03: item em LOGIN_ERROR no agregador → requer_reauth, sem importar."""
    user_id, conn_id = _seed_connection(db_session, email="reauth@e.com")
    base = _fake_with_data()
    adapter = FakeFinancialDataAdapter(
        accounts=base._accounts,
        transactions=base._transactions,
        item=ProviderItem(provider_item_id="i", status="LOGIN_ERROR"),
    )
    service = _make_service(db_session, adapter)

    result = service.sync(connection_id=conn_id, user_id=user_id)

    assert result.status == ConnectionStatus.REQUER_REAUTH.value
    assert result.imported == 0
    count = db_session.query(TransactionModel).filter_by(connection_id=conn_id).count()
    assert count == 0
    conn = SqlConnectionRepository(db_session).get(conn_id, user_id)
    assert conn is not None and conn.status == ConnectionStatus.REQUER_REAUTH


def test_sync_recovers_after_transient_errors(db_session: Session) -> None:
    user_id, conn_id = _seed_connection(db_session, email="sync4@e.com")

    class _FlakyAdapter(FakeFinancialDataAdapter):
        def __init__(self, **kw) -> None:
            super().__init__(**kw)
            self.calls = 0

        def fetch_accounts(self, *, provider_item_id: str):
            self.calls += 1
            if self.calls < 3:
                raise RetryableAggregatorError("429")
            return super().fetch_accounts(provider_item_id=provider_item_id)

    base = _fake_with_data()
    flaky = _FlakyAdapter(
        accounts=base._accounts, transactions=base._transactions
    )
    service = _make_service(db_session, flaky)

    result = service.sync(connection_id=conn_id, user_id=user_id)

    assert result.imported == 2
    assert flaky.calls == 3  # 2 falhas + 1 sucesso


def test_sync_marks_error_and_logs_on_fatal(db_session: Session) -> None:
    user_id, conn_id = _seed_connection(db_session, email="sync5@e.com")

    class _BrokenAdapter(FakeFinancialDataAdapter):
        def fetch_accounts(self, *, provider_item_id: str):
            raise AggregatorError("boom")

    service = _make_service(db_session, _BrokenAdapter())

    with pytest.raises(SyncFailed):
        service.sync(connection_id=conn_id, user_id=user_id)

    conn = SqlConnectionRepository(db_session).get(conn_id, user_id)
    assert conn is not None and conn.status == ConnectionStatus.ERRO
    log = (
        db_session.query(SyncLogModel)
        .filter_by(connection_id=conn_id, status="erro")
        .first()
    )
    assert log is not None and log.error is not None
