"""Entidade Connection e expiração de consentimento (base do RN-03)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.connection import Connection, ConnectionStatus


def _conn(expires_at: datetime | None) -> Connection:
    return Connection(
        id=uuid4(),
        user_id=uuid4(),
        provider="pluggy",
        provider_item_id="item-1",
        institution_name="Banco X",
        status=ConnectionStatus.ATIVA,
        consent_expires_at=expires_at,
    )


def test_consent_not_expired_when_future() -> None:
    now = datetime.now(UTC)
    conn = _conn(now + timedelta(days=1))
    assert conn.is_consent_expired(now) is False


def test_consent_expired_when_past() -> None:
    now = datetime.now(UTC)
    conn = _conn(now - timedelta(seconds=1))
    assert conn.is_consent_expired(now) is True


def test_consent_without_expiry_never_expires() -> None:
    assert _conn(None).is_consent_expired(datetime.now(UTC)) is False
