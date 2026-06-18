"""API de categorias, regras e recategorização (F7)."""

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


def _auth(client: TestClient, email: str = "f7@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_list_categories_includes_seed(client: TestClient) -> None:
    headers = _auth(client)
    resp = client.get("/categories", headers=headers)
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert "Outros" in names


def test_create_category_and_rule(client: TestClient) -> None:
    headers = _auth(client)
    cat = client.post(
        "/categories",
        headers=headers,
        json={"name": "Streaming", "kind": "expense"},
    )
    assert cat.status_code == 201
    cat_id = cat.json()["id"]

    rule = client.post(
        "/rules",
        headers=headers,
        json={"match_type": "contains", "pattern": "netflix", "category_id": cat_id},
    )
    assert rule.status_code == 201

    rules = client.get("/rules", headers=headers).json()
    assert len(rules) == 1


def test_rule_with_invalid_category_404(client: TestClient) -> None:
    headers = _auth(client)
    resp = client.post(
        "/rules",
        headers=headers,
        json={
            "match_type": "contains",
            "pattern": "x",
            "category_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert resp.status_code == 404


def _seed_tx(client: TestClient, headers: dict[str, str]) -> str:
    pa = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="CC",
        currency="BRL",
        balance=Decimal("0"),
    )
    pt = ProviderTransaction(
        provider_transaction_id="t1",
        date=date(2026, 1, 1),
        amount=Decimal("-50"),
        description="NETFLIX.COM assinatura",
    )
    fake = FakeFinancialDataAdapter(accounts=[pa], transactions={"acc-1": [pt]})
    with _override_adapter(fake):
        client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "i", "institution_name": "B"},
        )
        cid = client.get("/connections", headers=headers).json()[0]["id"]
        client.post(f"/connections/{cid}/sync", headers=headers)
    return client.get("/transactions", headers=headers).json()["items"][0]["id"]


def test_recategorize_changes_only_category(client: TestClient) -> None:
    headers = _auth(client)
    tx_id = _seed_tx(client, headers)
    cat_id = client.post(
        "/categories", headers=headers, json={"name": "Streaming", "kind": "expense"}
    ).json()["id"]

    resp = client.patch(
        f"/transactions/{tx_id}", headers=headers, json={"category_id": cat_id}
    )
    assert resp.status_code == 200
    assert resp.json()["category_id"] == cat_id
    assert resp.json()["category_name"] == "Streaming"


def test_recategorize_with_create_rule(client: TestClient) -> None:
    headers = _auth(client)
    tx_id = _seed_tx(client, headers)
    cat_id = client.post(
        "/categories", headers=headers, json={"name": "Streaming", "kind": "expense"}
    ).json()["id"]

    client.patch(
        f"/transactions/{tx_id}",
        headers=headers,
        json={"category_id": cat_id, "create_rule": True},
    )
    rules = client.get("/rules", headers=headers).json()
    assert len(rules) == 1
    assert rules[0]["category_id"] == cat_id


def test_sync_applies_rule_category(client: TestClient) -> None:
    headers = _auth(client)
    # cria categoria + regra ANTES de sincronizar
    cat_id = client.post(
        "/categories", headers=headers, json={"name": "Streaming", "kind": "expense"}
    ).json()["id"]
    client.post(
        "/rules",
        headers=headers,
        json={"match_type": "contains", "pattern": "netflix", "category_id": cat_id},
    )
    _seed_tx(client, headers)

    items = client.get("/transactions?q=netflix", headers=headers).json()["items"]
    assert items[0]["category_id"] == cat_id
    assert items[0]["category_name"] == "Streaming"
