"""Adapter fake do FinancialDataPort — para testes de integração e
resiliência (F5). Sem I/O; dados em memória."""

from datetime import date as date_type

from app.ports.financial_data_port import (
    ProviderAccount,
    ProviderItem,
    ProviderTransaction,
)


class FakeFinancialDataAdapter:
    def __init__(
        self,
        *,
        accounts: list[ProviderAccount] | None = None,
        transactions: dict[str, list[ProviderTransaction]] | None = None,
        connect_token: str = "fake-connect-token",
        item: ProviderItem | None = None,
    ) -> None:
        self._accounts = accounts or []
        self._transactions = transactions or {}
        self._connect_token = connect_token
        self._item = item

    def create_connect_token(
        self,
        *,
        item_id: str | None = None,
        webhook_url: str | None = None,
        client_user_id: str | None = None,
    ) -> str:
        return self._connect_token

    def fetch_item(self, *, provider_item_id: str) -> ProviderItem:
        # Default: item saudável (UPDATED) para não alterar fluxos de teste.
        return self._item or ProviderItem(
            provider_item_id=provider_item_id, status="UPDATED"
        )

    def fetch_accounts(self, *, provider_item_id: str) -> list[ProviderAccount]:
        return list(self._accounts)

    def fetch_transactions(
        self,
        *,
        provider_item_id: str,
        provider_account_id: str,
        since: date_type | None = None,
    ) -> list[ProviderTransaction]:
        return list(self._transactions.get(provider_account_id, []))
