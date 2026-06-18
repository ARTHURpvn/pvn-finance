"""PluggyAdapter — implementa FinancialDataPort sobre a API do Pluggy.

Traduz os payloads do Pluggy (forma "provider") para os DTOs canônicos
do Open Finance. O domínio não conhece este módulo (ADR-002)."""

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from app.ports.financial_data_port import ProviderAccount, ProviderTransaction

#: subtype do Pluggy → AccountType do domínio (valor string).
_SUBTYPE_TO_TYPE: dict[str, str] = {
    "CHECKING_ACCOUNT": "checking",
    "SAVINGS_ACCOUNT": "savings",
    "CREDIT_CARD": "credit_card",
}
_DEFAULT_ACCOUNT_TYPE = "payment"


class PluggyError(Exception):
    """Falha na comunicação com o Pluggy."""


def _parse_date(value: str) -> date_type:
    """Converte data ISO-8601 do Pluggy (com 'Z') para date."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


class PluggyAdapter:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.pluggy.ai",
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http_client or httpx.Client(base_url=base_url, timeout=30.0)
        self._api_key: str | None = None

    # ---- autenticação -----------------------------------------------------

    def _authenticate(self) -> str:
        resp = self._http.post(
            "/auth",
            json={"clientId": self._client_id, "clientSecret": self._client_secret},
        )
        resp.raise_for_status()
        self._api_key = resp.json()["apiKey"]
        return self._api_key

    def _headers(self) -> dict[str, str]:
        if self._api_key is None:
            self._authenticate()
        assert self._api_key is not None
        return {"X-API-KEY": self._api_key}

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        resp = self._http.get(path, params=params, headers=self._headers())
        if resp.status_code == httpx.codes.UNAUTHORIZED:
            # apiKey pode ter expirado — reautentica uma vez.
            self._api_key = None
            resp = self._http.get(path, params=params, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    # ---- widget -----------------------------------------------------------

    def create_connect_token(self, *, item_id: str | None = None) -> str:
        """Emite o accessToken do Pluggy Connect (FR-003). Com `item_id`,
        habilita o fluxo de reautenticação (FR-005)."""
        body = {"itemId": item_id} if item_id else {}
        resp = self._http.post("/connect_token", json=body, headers=self._headers())
        resp.raise_for_status()
        return resp.json()["accessToken"]

    # ---- FinancialDataPort ------------------------------------------------

    def fetch_accounts(self, *, provider_item_id: str) -> list[ProviderAccount]:
        data = self._get("/accounts", {"itemId": provider_item_id})
        return [self._map_account(r) for r in data.get("results", [])]

    def fetch_transactions(
        self,
        *,
        provider_item_id: str,
        provider_account_id: str,
        since: date_type | None = None,
    ) -> list[ProviderTransaction]:
        params: dict[str, Any] = {"accountId": provider_account_id}
        if since is not None:
            params["startDate"] = since.isoformat()
        data = self._get("/transactions", params)
        return [self._map_transaction(r) for r in data.get("results", [])]

    # ---- mapeamento -------------------------------------------------------

    @staticmethod
    def _map_account(raw: dict[str, Any]) -> ProviderAccount:
        subtype = (raw.get("subtype") or "").upper()
        return ProviderAccount(
            provider_account_id=raw["id"],
            type=_SUBTYPE_TO_TYPE.get(subtype, _DEFAULT_ACCOUNT_TYPE),
            name=raw.get("name") or raw.get("marketingName") or "Conta",
            currency=raw.get("currencyCode") or "BRL",
            balance=Decimal(str(raw.get("balance", "0"))),
        )

    @staticmethod
    def _map_transaction(raw: dict[str, Any]) -> ProviderTransaction:
        # O Pluggy já entrega `amount` assinado (DEBIT negativo); RN-01 deriva
        # a direção a partir do sinal na normalização.
        return ProviderTransaction(
            provider_transaction_id=raw["id"],
            date=_parse_date(raw["date"]),
            amount=Decimal(str(raw["amount"])),
            description=raw.get("description") or raw.get("descriptionRaw") or "",
            counterpart=(raw.get("merchant") or {}).get("name"),
            provider_category=raw.get("category"),
            raw=raw,
        )
