"""ConnectionService — orquestra o ciclo de vida das conexões."""

from uuid import UUID

from app.domain.connection import Connection
from app.ports.financial_data_port import AggregatorError, FinancialDataPort
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
        webhook_url: str | None = None,
    ) -> None:
        self._adapter = adapter
        self._connections = connections
        self._provider = provider
        self._webhook_url = webhook_url

    def create_connect_token(self, user_id: UUID) -> str:
        """Inicia uma conexão: emite o token do widget (FR-003), já inscrito
        no webhook e vinculado ao usuário."""
        return self._adapter.create_connect_token(
            webhook_url=self._webhook_url, client_user_id=str(user_id)
        )

    def register(
        self, *, user_id: UUID, provider_item_id: str, institution_name: str
    ) -> Connection:
        """Persiste a conexão após o usuário concluir o widget, já lendo o
        consentimento do item (RN-03) quando disponível."""
        existing = self._connections.get_by_provider_item(
            self._provider, provider_item_id
        )
        if existing is not None:
            raise ConnectionAlreadyExists
        consent_expires_at = None
        try:
            item = self._adapter.fetch_item(provider_item_id=provider_item_id)
            consent_expires_at = item.consent_expires_at
        except AggregatorError:
            # Item pode ainda estar coletando; registra sem consentimento e a
            # próxima sync/webhook reconcilia o status.
            pass
        return self._connections.add(
            user_id=user_id,
            provider=self._provider,
            provider_item_id=provider_item_id,
            institution_name=institution_name,
            consent_expires_at=consent_expires_at,
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
        return self._adapter.create_connect_token(
            item_id=connection.provider_item_id,
            webhook_url=self._webhook_url,
            client_user_id=str(user_id),
        )

    def delete(self, connection_id: UUID, user_id: UUID) -> None:
        """Revoga a conexão e apaga os dados associados (FR-006)."""
        if not self._connections.delete(connection_id, user_id):
            raise ConnectionNotFound
