"""Webhook /webhooks/pluggy (F9) — auth por header, idempotência, reconciliação."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import app.api.webhooks as webhooks
from app.adapters.fake import FakeFinancialDataAdapter
from app.api.deps import get_financial_adapter
from app.config import get_settings
from app.main import app
from app.ports.financial_data_port import ProviderItem


@pytest.fixture(autouse=True)
def _reset_webhook_state() -> Iterator[None]:
    """Isola o dedupe de eventId e o cache de settings entre testes, e provê
    um adapter fake às rotas (register/connections precisam do agregador)."""
    webhooks._seen_events._seen.clear()
    get_settings.cache_clear()
    app.dependency_overrides[get_financial_adapter] = lambda: FakeFinancialDataAdapter()
    yield
    app.dependency_overrides.pop(get_financial_adapter, None)
    webhooks._seen_events._seen.clear()
    get_settings.cache_clear()


def _use_background_adapter(monkeypatch: pytest.MonkeyPatch, adapter) -> None:
    """O sync em background usa make_financial_adapter (fora do request)."""
    monkeypatch.setattr(webhooks, "make_financial_adapter", lambda: adapter)


def _register_item(client: TestClient, headers: dict[str, str], item_id: str) -> None:
    resp = client.post(
        "/connections/register",
        headers=headers,
        json={"provider_item_id": item_id, "institution_name": "B"},
    )
    assert resp.status_code == 201, resp.text


def _auth(client: TestClient, email: str = "wh@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_webhook_unknown_item_is_accepted_not_synced(client: TestClient) -> None:
    resp = client.post(
        "/webhooks/pluggy", json={"event": "item/updated", "itemId": "nope"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"received": True, "handled": False}


def test_webhook_known_item_triggers_sync(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _auth(client)
    _register_item(client, headers, "item-wh-1")
    _use_background_adapter(monkeypatch, FakeFinancialDataAdapter())

    resp = client.post(
        "/webhooks/pluggy",
        json={"event": "item/updated", "eventId": "e1", "itemId": "item-wh-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["handled"] is True
    conns = client.get("/connections", headers=headers).json()
    assert conns[0]["status"] == "ativa"


def test_webhook_item_error_reconciles_to_reauth(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """item/error → GET /items reconcilia; LOGIN_ERROR vira requer_reauth."""
    headers = _auth(client, email="wherr@e.com")
    _register_item(client, headers, "item-err-1")
    adapter = FakeFinancialDataAdapter(
        item=ProviderItem(provider_item_id="item-err-1", status="LOGIN_ERROR")
    )
    _use_background_adapter(monkeypatch, adapter)

    resp = client.post(
        "/webhooks/pluggy",
        json={"event": "item/error", "eventId": "e2", "itemId": "item-err-1"},
    )

    assert resp.status_code == 200
    assert resp.json()["handled"] is True
    conns = client.get("/connections", headers=headers).json()
    assert conns[0]["status"] == "requer_reauth"


def test_webhook_dedupes_repeated_event_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _auth(client, email="wdup@e.com")
    _register_item(client, headers, "item-dup-1")
    _use_background_adapter(monkeypatch, FakeFinancialDataAdapter())

    first = client.post(
        "/webhooks/pluggy",
        json={"event": "item/updated", "eventId": "dup-1", "itemId": "item-dup-1"},
    )
    second = client.post(
        "/webhooks/pluggy",
        json={"event": "item/updated", "eventId": "dup-1", "itemId": "item-dup-1"},
    )

    assert first.json()["handled"] is True
    assert second.json()["handled"] is False  # reentrega ignorada


@pytest.mark.parametrize("event", ["item/created", "item/login_succeeded"])
def test_webhook_ignores_premature_events(client: TestClient, event: str) -> None:
    headers = _auth(client, email="wprem@e.com")
    _register_item(client, headers, "item-prem-1")
    resp = client.post(
        "/webhooks/pluggy",
        json={"event": event, "itemId": "item-prem-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["handled"] is False


def test_webhook_ignores_unrelated_event(client: TestClient) -> None:
    headers = _auth(client, email="wign@e.com")
    _register_item(client, headers, "item-ign-1")
    resp = client.post(
        "/webhooks/pluggy",
        json={"event": "connector/status_updated", "itemId": "item-ign-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["handled"] is False


def test_webhook_invalid_payload_400(client: TestClient) -> None:
    resp = client.post(
        "/webhooks/pluggy",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_webhook_header_secret_auth(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PLUGGY_WEBHOOK_SECRET", "whsecret")
    monkeypatch.setenv("PLUGGY_WEBHOOK_HEADER", "x-webhook-secret")
    get_settings.cache_clear()

    body = {"event": "item/updated", "itemId": "y"}
    # sem header → 401
    assert client.post("/webhooks/pluggy", json=body).status_code == 401
    # header errado → 401
    bad = client.post(
        "/webhooks/pluggy", json=body, headers={"x-webhook-secret": "nope"}
    )
    assert bad.status_code == 401
    # header correto → 200 (item desconhecido, mas autenticado)
    ok = client.post(
        "/webhooks/pluggy", json=body, headers={"x-webhook-secret": "whsecret"}
    )
    assert ok.status_code == 200


def test_webhook_rejects_oversized_body(client: TestClient) -> None:
    huge = {"event": "item/updated", "itemId": "x", "pad": "a" * (70 * 1024)}
    resp = client.post("/webhooks/pluggy", json=huge)
    assert resp.status_code == 413
