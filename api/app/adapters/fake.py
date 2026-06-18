"""Adapter fake do FinancialDataPort — para testes de integração e
resiliência (F5). Sem I/O; dados em memória."""

from datetime import date as date_type

from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


class FakeFinancialDataAdapter:
    def __init__(
        self,
        *,
        accounts: list[ProviderAccount] | None = None,
        transactions: dict[str, list[ProviderTransaction]] | None = None,
        connect_token: str = "fake-connect-token",
    ) -> None:
        self._accounts = accounts or []
        self._transactions = transactions or {}
        self._connect_token = connect_token

    def create_connect_token(self, *, item_id: str | None = None) -> str:
        return self._connect_token

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
