"""PluggyAdapter — implementa FinancialDataPort sobre a API do Pluggy.

Traduz os payloads do Pluggy (forma "provider") para os DTOs canônicos
do Open Finance. O domínio não conhece este módulo (ADR-002)."""

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from app.ports.financial_data_port import (
    AggregatorError,
    ProviderAccount,
    ProviderTransaction,
    RetryableAggregatorError,
)

#: subtype do Pluggy → AccountType do domínio (valor string).
_SUBTYPE_TO_TYPE: dict[str, str] = {
    "CHECKING_ACCOUNT": "checking",
    "SAVINGS_ACCOUNT": "savings",
    "CREDIT_CARD": "credit_card",
}
_DEFAULT_ACCOUNT_TYPE = "payment"

#: Status HTTP transitórios que justificam retry com backoff (NFR-004).
_RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}


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

    # ---- transporte / tradução de erros -----------------------------------

    @staticmethod
    def _handle(resp: httpx.Response) -> httpx.Response:
        if resp.status_code in _RETRYABLE_STATUS:
            raise RetryableAggregatorError(f"pluggy retornou {resp.status_code}")
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AggregatorError(str(exc)) from exc
        return resp

    def _post(
        self, path: str, *, json: dict[str, Any], headers: dict[str, str] | None = None
    ) -> httpx.Response:
        try:
            return self._http.post(path, json=json, headers=headers)
        except httpx.TransportError as exc:
            raise RetryableAggregatorError(str(exc)) from exc

    def _get_raw(
        self, path: str, params: dict[str, Any], headers: dict[str, str]
    ) -> httpx.Response:
        # params vazio + path já com query (cursor) faz o httpx descartar a
        # query; só repassamos params quando há algo.
        kwargs: dict[str, Any] = {"headers": headers}
        if params:
            kwargs["params"] = params
        try:
            return self._http.get(path, **kwargs)
        except httpx.TransportError as exc:
            raise RetryableAggregatorError(str(exc)) from exc

    # ---- autenticação -----------------------------------------------------

    def _authenticate(self) -> str:
        resp = self._handle(
            self._post(
                "/auth",
                json={
                    "clientId": self._client_id,
                    "clientSecret": self._client_secret,
                },
            )
        )
        self._api_key = resp.json()["apiKey"]
        return self._api_key

    def _headers(self) -> dict[str, str]:
        if self._api_key is None:
            self._authenticate()
        assert self._api_key is not None
        return {"X-API-KEY": self._api_key}

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        resp = self._get_raw(path, params, self._headers())
        if resp.status_code == httpx.codes.UNAUTHORIZED:
            # apiKey pode ter expirado — reautentica uma vez.
            self._api_key = None
            resp = self._get_raw(path, params, self._headers())
        return self._handle(resp).json()

    # ---- widget -----------------------------------------------------------

    def create_connect_token(self, *, item_id: str | None = None) -> str:
        """Emite o accessToken do Pluggy Connect (FR-003). Com `item_id`,
        habilita o fluxo de reautenticação (FR-005)."""
        body = {"itemId": item_id} if item_id else {}
        resp = self._handle(self._post("/connect_token", json=body, headers=self._headers()))
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
        # Usa /v2/transactions (cursor): o /transactions v1 foi descontinuado
        # pelo Pluggy (responde 410 Gone).
        params: dict[str, Any] = {"accountId": provider_account_id}
        if since is not None:
            params["dateFrom"] = since.isoformat()

        data = self._get("/v2/transactions", params)
        results: list[dict[str, Any]] = list(data.get("results", []))

        next_query = data.get("next")
        pages = 0
        while next_query and pages < 100:
            path = (
                f"/v2/transactions{next_query}"
                if next_query.startswith("?")
                else next_query
            )
            data = self._get(path, {})
            results.extend(data.get("results", []))
            next_query = data.get("next")
            pages += 1

        return [self._map_transaction(r) for r in results]

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
