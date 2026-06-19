"""Webhook /webhooks/pluggy (F9)."""

import hashlib
import hmac
import json
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.adapters.fake import FakeFinancialDataAdapter
from app.api.deps import get_financial_adapter
from app.config import get_settings
from app.main import app


@contextmanager
def _override_adapter(adapter):
    app.dependency_overrides[get_financial_adapter] = lambda: adapter
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_financial_adapter, None)


def _auth(client: TestClient, email: str = "wh@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _register_item(client: TestClient, headers: dict[str, str], item_id: str) -> None:
    with _override_adapter(FakeFinancialDataAdapter()):
        client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": item_id, "institution_name": "B"},
        )


def test_webhook_unknown_item_is_accepted_not_synced(client: TestClient) -> None:
    resp = client.post("/webhooks/pluggy", json={"event": "item/updated", "itemId": "nope"})
    assert resp.status_code == 200
    assert resp.json() == {"received": True, "handled": False}


def test_webhook_known_item_triggers_sync(client: TestClient) -> None:
    headers = _auth(client)
    _register_item(client, headers, "item-wh-1")
    resp = client.post(
        "/webhooks/pluggy",
        json={"event": "item/updated", "eventId": "e1", "itemId": "item-wh-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["handled"] is True


def test_webhook_item_error_marks_connection(client: TestClient) -> None:
    headers = _auth(client, email="wherr@e.com")
    with _override_adapter(FakeFinancialDataAdapter()):
        client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "item-err-1", "institution_name": "B"},
        )
        resp = client.post(
            "/webhooks/pluggy",
            json={"event": "item/error", "eventId": "e2", "itemId": "item-err-1"},
        )
        assert resp.status_code == 200
        assert resp.json()["handled"] is True
        conns = client.get("/connections", headers=headers).json()
    assert conns[0]["status"] == "erro"


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


def test_webhook_signature_validation(client: TestClient) -> None:
    get_settings.cache_clear()
    import os

    os.environ["PLUGGY_WEBHOOK_SECRET"] = "whsecret"
    get_settings.cache_clear()
    try:
        body = json.dumps({"event": "x", "itemId": "y"}).encode()
        # sem assinatura → 401
        bad = client.post(
            "/webhooks/pluggy",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert bad.status_code == 401

        sig = hmac.new(b"whsecret", body, hashlib.sha256).hexdigest()
        ok = client.post(
            "/webhooks/pluggy",
            content=body,
            headers={"Content-Type": "application/json", "X-Webhook-Signature": sig},
        )
        assert ok.status_code == 200
    finally:
        del os.environ["PLUGGY_WEBHOOK_SECRET"]
        get_settings.cache_clear()
