"""Contrato do PluggyAdapter — mapeamento de payloads (sem rede)."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import httpx

from app.adapters.pluggy import PluggyAdapter

_FIXTURES = Path(__file__).parent.parent / "fixtures" / "pluggy"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _make_adapter(handler) -> PluggyAdapter:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="https://api.pluggy.test", transport=transport)
    return PluggyAdapter(
        client_id="cid", client_secret="secret", http_client=client
    )


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/auth":
        return httpx.Response(200, json={"apiKey": "fake-api-key"})
    if path == "/connect_token":
        return httpx.Response(200, json={"accessToken": "connect-abc"})
    if path == "/accounts":
        return httpx.Response(200, json=_load("accounts.json"))
    if path == "/v2/transactions":
        return httpx.Response(200, json=_load("transactions.json"))
    return httpx.Response(404)


def test_fetch_accounts_maps_types_and_balance() -> None:
    adapter = _make_adapter(_handler)

    accounts = adapter.fetch_accounts(provider_item_id="item-1")

    assert len(accounts) == 2
    checking = accounts[0]
    assert checking.type == "checking"
    assert checking.balance == Decimal("1209.50")
    assert checking.currency == "BRL"
    card = accounts[1]
    assert card.type == "credit_card"
    assert card.balance == Decimal("-450.00")


def test_fetch_transactions_maps_signed_amount_and_date() -> None:
    adapter = _make_adapter(_handler)

    txs = adapter.fetch_transactions(
        provider_item_id="item-1", provider_account_id="a658c848"
    )

    assert len(txs) == 2
    debit = txs[0]
    assert debit.amount == Decimal("-212.45")  # DEBIT assinado
    assert debit.date == date(2026, 1, 15)
    assert debit.provider_category == "Investimentos"
    credit = txs[1]
    assert credit.amount == Decimal("5000.00")
    assert credit.counterpart == "ACME LTDA"
    assert credit.raw is not None  # payload original preservado


def test_fetch_transactions_follows_cursor_pagination() -> None:
    page1 = {
        "results": [
            {
                "id": "p1",
                "description": "A",
                "amount": -1,
                "date": "2026-01-01T00:00:00.000Z",
                "type": "DEBIT",
            }
        ],
        "next": "?accountId=acc&after=cursor1",
    }
    page2 = {
        "results": [
            {
                "id": "p2",
                "description": "B",
                "amount": 2,
                "date": "2026-01-02T00:00:00.000Z",
                "type": "CREDIT",
            }
        ],
        "next": None,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth":
            return httpx.Response(200, json={"apiKey": "k"})
        if request.url.path == "/v2/transactions":
            body = page2 if "after=cursor1" in str(request.url) else page1
            return httpx.Response(200, json=body)
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    txs = adapter.fetch_transactions(
        provider_item_id="i", provider_account_id="acc"
    )

    assert [t.provider_transaction_id for t in txs] == ["p1", "p2"]


def test_create_connect_token() -> None:
    adapter = _make_adapter(_handler)
    assert adapter.create_connect_token() == "connect-abc"


def test_connect_token_sends_webhook_and_client_user_options() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth":
            return httpx.Response(200, json={"apiKey": "k"})
        if request.url.path == "/connect_token":
            captured.update(json.loads(request.content))
            return httpx.Response(200, json={"accessToken": "t"})
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    adapter.create_connect_token(
        item_id="it-1", webhook_url="https://x.test/wh", client_user_id="u-1"
    )

    assert captured["itemId"] == "it-1"
    assert captured["options"] == {
        "webhookUrl": "https://x.test/wh",
        "clientUserId": "u-1",
    }


def test_fetch_item_maps_status_and_consent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth":
            return httpx.Response(200, json={"apiKey": "k"})
        if request.url.path == "/items/it-9":
            return httpx.Response(
                200,
                json={
                    "id": "it-9",
                    "status": "LOGIN_ERROR",
                    "executionStatus": "INVALID_CREDENTIALS",
                    "consentExpiresAt": "2026-12-31T23:59:59.000Z",
                    "error": {"code": "INVALID_CREDENTIALS", "message": "x"},
                },
            )
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    item = adapter.fetch_item(provider_item_id="it-9")

    assert item.provider_item_id == "it-9"
    assert item.status == "LOGIN_ERROR"
    assert item.execution_status == "INVALID_CREDENTIALS"
    assert item.error_code == "INVALID_CREDENTIALS"
    assert item.consent_expires_at == datetime.fromisoformat(
        "2026-12-31T23:59:59+00:00"
    )


def test_reauthenticates_on_401() -> None:
    calls = {"auth": 0, "accounts": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/auth":
            calls["auth"] += 1
            return httpx.Response(200, json={"apiKey": f"key-{calls['auth']}"})
        if path == "/accounts":
            calls["accounts"] += 1
            if calls["accounts"] == 1:
                return httpx.Response(401, json={"message": "expired"})
            return httpx.Response(200, json=_load("accounts.json"))
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    accounts = adapter.fetch_accounts(provider_item_id="item-1")

    assert len(accounts) == 2
    assert calls["auth"] == 2  # reautenticou após o 401


def test_reauthenticates_on_403() -> None:
    """O Pluggy responde 403 (não 401) para apiKey expirada/inválida."""
    calls = {"auth": 0, "accounts": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/auth":
            calls["auth"] += 1
            return httpx.Response(200, json={"apiKey": f"key-{calls['auth']}"})
        if path == "/accounts":
            calls["accounts"] += 1
            if calls["accounts"] == 1:
                return httpx.Response(
                    403, json={"code": 403, "message": "invalid token"}
                )
            return httpx.Response(200, json=_load("accounts.json"))
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    accounts = adapter.fetch_accounts(provider_item_id="item-1")

    assert len(accounts) == 2
    assert calls["auth"] == 2  # reautenticou após o 403


def test_reauthenticates_on_403_for_connect_token() -> None:
    calls = {"auth": 0, "ct": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/auth":
            calls["auth"] += 1
            return httpx.Response(200, json={"apiKey": f"key-{calls['auth']}"})
        if path == "/connect_token":
            calls["ct"] += 1
            if calls["ct"] == 1:
                return httpx.Response(403, json={"code": 403, "message": "x"})
            return httpx.Response(200, json={"accessToken": "ok"})
        return httpx.Response(404)

    adapter = _make_adapter(handler)
    token = adapter.create_connect_token()

    assert token == "ok"
    assert calls["auth"] == 2  # POST também reautentica


def test_retry_after_header_propagates_to_error() -> None:
    from app.ports.financial_data_port import RetryableAggregatorError

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth":
            return httpx.Response(200, json={"apiKey": "k"})
        return httpx.Response(429, headers={"Retry-After": "7"}, json={})

    adapter = _make_adapter(handler)
    try:
        adapter.fetch_accounts(provider_item_id="item-1")
    except RetryableAggregatorError as exc:
        assert exc.retry_after == 7.0
    else:  # pragma: no cover
        raise AssertionError("esperava RetryableAggregatorError")
