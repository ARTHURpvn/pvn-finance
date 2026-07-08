"""Entidade Connection e expiração de consentimento (base do RN-03)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.connection import (
    Connection,
    ConnectionStatus,
    connection_status_from_item,
)


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


class TestConnectionStatusFromItem:
    """Mapeamento status do Item (Pluggy) → status da conexão (RN-03)."""

    _now = datetime.now(UTC)

    @pytest.mark.parametrize(
        "item_status,expected",
        [
            ("UPDATED", ConnectionStatus.ATIVA),
            ("LOGIN_ERROR", ConnectionStatus.REQUER_REAUTH),
            ("WAITING_USER_INPUT", ConnectionStatus.REQUER_REAUTH),
            ("WAITING_USER_ACTION", ConnectionStatus.REQUER_REAUTH),
            ("OUTDATED", ConnectionStatus.ERRO),
            ("ERROR", ConnectionStatus.ERRO),
            ("login_error", ConnectionStatus.REQUER_REAUTH),  # case-insensitive
        ],
    )
    def test_maps_terminal_statuses(
        self, item_status: str, expected: ConnectionStatus
    ) -> None:
        result = connection_status_from_item(
            item_status, consent_expires_at=None, now=self._now
        )
        assert result == expected

    @pytest.mark.parametrize("item_status", ["UPDATING", "LOGIN_IN_PROGRESS", "WTF"])
    def test_in_progress_or_unknown_returns_none(self, item_status: str) -> None:
        result = connection_status_from_item(
            item_status, consent_expires_at=None, now=self._now
        )
        assert result is None

    def test_expired_consent_takes_precedence_over_updated(self) -> None:
        result = connection_status_from_item(
            "UPDATED",
            consent_expires_at=self._now - timedelta(seconds=1),
            now=self._now,
        )
        assert result == ConnectionStatus.REQUER_REAUTH

    def test_future_consent_does_not_override_ok(self) -> None:
        result = connection_status_from_item(
            "UPDATED",
            consent_expires_at=self._now + timedelta(days=30),
            now=self._now,
        )
        assert result == ConnectionStatus.ATIVA
