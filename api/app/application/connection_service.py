"""ConnectionService — orquestra o ciclo de vida das conexões."""

from uuid import UUID

from app.domain.connection import Connection
from app.ports.financial_data_port import FinancialDataPort
from app.ports.repositories import ConnectionRepository


class ConnectionNotFound(Exception):
    """Conexão inexistente ou de outro usuário."""


class ConnectionAlreadyExists(Exception):
    """Já existe conexão para este provider_item_id."""


class ConnectionService:
    def __init__(
        self,
        *,
        adapter: FinancialDataPort,
        connections: ConnectionRepository,
        provider: str = "pluggy",
    ) -> None:
        self._adapter = adapter
        self._connections = connections
        self._provider = provider

    def create_connect_token(self) -> str:
        """Inicia uma conexão: emite o token do widget (FR-003)."""
        return self._adapter.create_connect_token()

    def register(
        self, *, user_id: UUID, provider_item_id: str, institution_name: str
    ) -> Connection:
        """Persiste a conexão após o usuário concluir o widget."""
        existing = self._connections.get_by_provider_item(
            self._provider, provider_item_id
        )
        if existing is not None:
            raise ConnectionAlreadyExists
        return self._connections.add(
            user_id=user_id,
            provider=self._provider,
            provider_item_id=provider_item_id,
            institution_name=institution_name,
        )

    def list(self, user_id: UUID) -> list[Connection]:
        return self._connections.list(user_id)

    def get(self, connection_id: UUID, user_id: UUID) -> Connection:
        connection = self._connections.get(connection_id, user_id)
        if connection is None:
            raise ConnectionNotFound
        return connection

    def reauth_token(self, connection_id: UUID, user_id: UUID) -> str:
        """Emite connect token vinculado ao item para reautenticação (FR-005)."""
        connection = self.get(connection_id, user_id)
        return self._adapter.create_connect_token(item_id=connection.provider_item_id)

    def delete(self, connection_id: UUID, user_id: UUID) -> None:
        """Revoga a conexão e apaga os dados associados (FR-006)."""
        if not self._connections.delete(connection_id, user_id):
            raise ConnectionNotFound
