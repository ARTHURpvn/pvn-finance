"""API de conexões (F5) — integração com adapter fake injetado."""

from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.adapters.fake import FakeFinancialDataAdapter
from app.api.deps import get_financial_adapter
from app.main import app
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


@contextmanager
def _override_adapter(adapter):
    app.dependency_overrides[get_financial_adapter] = lambda: adapter
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_financial_adapter, None)


def _auth(client: TestClient, email: str = "owner@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _fake() -> FakeFinancialDataAdapter:
    pa = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="Conta",
        currency="BRL",
        balance=Decimal("100.00"),
    )
    pt = ProviderTransaction(
        provider_transaction_id="t1",
        date=date(2026, 1, 1),
        amount=Decimal("-10.00"),
        description="x",
    )
    return FakeFinancialDataAdapter(
        accounts=[pa], transactions={"acc-1": [pt]}, connect_token="tok-123"
    )


def test_connections_require_auth(client: TestClient) -> None:
    assert client.get("/connections").status_code == 401


def test_start_connection_returns_token(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        resp = client.post("/connections", headers=headers)
    assert resp.status_code == 201
    assert resp.json()["connect_token"] == "tok-123"


def test_register_list_and_sync(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        reg = client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "item-1", "institution_name": "Banco X"},
        )
        assert reg.status_code == 201
        conn_id = reg.json()["id"]

        listing = client.get("/connections", headers=headers)
        assert listing.status_code == 200
        assert len(listing.json()) == 1

        synced = client.post(f"/connections/{conn_id}/sync", headers=headers)
        assert synced.status_code == 200
        assert synced.json() == {"status": "ativa", "imported": 1}

        again = client.post(f"/connections/{conn_id}/sync", headers=headers)
        assert again.json()["imported"] == 0  # dedupe


def test_register_duplicate_returns_409(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        body = {"provider_item_id": "item-dup", "institution_name": "B"}
        client.post("/connections/register", headers=headers, json=body)
        dup = client.post("/connections/register", headers=headers, json=body)
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "connection_exists"


def test_cannot_access_other_users_connection(client: TestClient) -> None:
    headers_a = _auth(client, email="alice@e.com")
    with _override_adapter(_fake()):
        reg = client.post(
            "/connections/register",
            headers=headers_a,
            json={"provider_item_id": "item-a", "institution_name": "B"},
        )
        conn_id = reg.json()["id"]
        headers_b = _auth(client, email="bob@e.com")
        resp = client.get(f"/connections/{conn_id}", headers=headers_b)
    assert resp.status_code == 404


def test_delete_removes_connection(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        reg = client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "item-del", "institution_name": "B"},
        )
        conn_id = reg.json()["id"]
        client.post(f"/connections/{conn_id}/sync", headers=headers)
        deleted = client.delete(f"/connections/{conn_id}", headers=headers)
        assert deleted.status_code == 204
        gone = client.get(f"/connections/{conn_id}", headers=headers)
    assert gone.status_code == 404


def test_reauth_returns_token(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        reg = client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "item-r", "institution_name": "B"},
        )
        conn_id = reg.json()["id"]
        resp = client.post(f"/connections/{conn_id}/reauth", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["connect_token"] == "tok-123"
