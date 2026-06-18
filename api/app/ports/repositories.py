"""Ports dos repositórios usados pelos serviços de aplicação.

Os adapters SQLAlchemy em infrastructure satisfazem estes contratos
estruturalmente (Protocol), mantendo a aplicação livre de SQLAlchemy."""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domain.account import Account
from app.domain.connection import Connection, ConnectionStatus
from app.domain.transaction import Transaction
from app.ports.financial_data_port import ProviderAccount


class ConnectionRepository(Protocol):
    def add(
        self,
        *,
        user_id: UUID,
        provider: str,
        provider_item_id: str,
        institution_name: str,
        status: ConnectionStatus = ...,
        encrypted_secret: bytes | None = ...,
        consent_expires_at: datetime | None = ...,
    ) -> Connection: ...
    def get(self, connection_id: UUID, user_id: UUID) -> Connection | None: ...
    def get_by_provider_item(
        self, provider: str, provider_item_id: str
    ) -> Connection | None: ...
    def list(self, user_id: UUID) -> list[Connection]: ...
    def set_status(self, connection_id: UUID, status: ConnectionStatus) -> None: ...
    def mark_synced(
        self, connection_id: UUID, when: datetime, *, status: ConnectionStatus = ...
    ) -> None: ...
    def delete(self, connection_id: UUID, user_id: UUID) -> bool: ...


class AccountRepository(Protocol):
    def upsert(
        self, *, user_id: UUID, connection_id: UUID, provider_account: ProviderAccount
    ) -> Account: ...
    def list_by_user(self, user_id: UUID) -> list[Account]: ...


class TransactionRepository(Protocol):
    def existing_provider_ids(self, connection_id: UUID) -> set[str]: ...
    def add_many(
        self,
        connection_id: UUID,
        items: list[tuple[Transaction, dict[str, Any] | None]],
    ) -> int: ...


class SyncLogRepository(Protocol):
    def start(self, connection_id: UUID) -> UUID: ...
    def finish(
        self, log_id: UUID, *, status: str, error: str | None = None
    ) -> None: ...
