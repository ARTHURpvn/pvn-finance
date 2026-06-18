"""Varredura de sync agendada (F9)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.adapters.fake import FakeFinancialDataAdapter
from app.application.scheduler import sync_due_connections
from app.domain.connection import ConnectionStatus
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.models import TransactionModel
from app.infrastructure.user_repository import SqlUserRepository
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


def _fake() -> FakeFinancialDataAdapter:
    pa = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="CC",
        currency="BRL",
        balance=Decimal("0"),
    )
    pt = ProviderTransaction(
        provider_transaction_id="t1",
        date=datetime(2026, 1, 1).date(),
        amount=Decimal("-10"),
        description="x",
    )
    return FakeFinancialDataAdapter(accounts=[pa], transactions={"acc-1": [pt]})


def _make_connection(session: Session, email: str):
    user = SqlUserRepository(session).add(email=email, password_hash="x")
    return SqlConnectionRepository(session).add(
        user_id=user.id,
        provider="pluggy",
        provider_item_id=f"item-{email}",
        institution_name="B",
    )


def test_sweep_syncs_due_connection(db_session: Session) -> None:
    conn = _make_connection(db_session, "sched1@e.com")

    result = sync_due_connections(
        session=db_session, adapter=_fake(), now=datetime.now(UTC), stale_minutes=60
    )

    assert result.succeeded >= 1
    # a conexão recém-criada (sem last_sync) foi sincronizada
    refreshed = SqlConnectionRepository(db_session).get(conn.id, conn.user_id)
    assert refreshed is not None and refreshed.last_sync_at is not None
    count = db_session.query(TransactionModel).filter_by(connection_id=conn.id).count()
    assert count == 1


def test_list_due_excludes_recently_synced(db_session: Session) -> None:
    conn = _make_connection(db_session, "sched2@e.com")
    repo = SqlConnectionRepository(db_session)
    now = datetime.now(UTC)

    # sem last_sync → devida
    threshold = now - timedelta(minutes=60)
    assert any(c.id == conn.id for c in repo.list_due(threshold))

    # após sync recente → não devida
    repo.mark_synced(conn.id, now, status=ConnectionStatus.ATIVA)
    assert all(c.id != conn.id for c in repo.list_due(threshold))
