"""API de contas e transações (F6) — com dados semeados via sync (fake)."""

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


def _auth(client: TestClient, email: str = "f6@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _fake() -> FakeFinancialDataAdapter:
    accounts = [
        ProviderAccount(
            provider_account_id="chk",
            type="checking",
            name="Conta Corrente",
            currency="BRL",
            balance=Decimal("1000.00"),
        ),
        ProviderAccount(
            provider_account_id="cc",
            type="credit_card",
            name="Cartão",
            currency="BRL",
            balance=Decimal("-200.00"),
        ),
    ]
    txs = {
        "chk": [
            ProviderTransaction(
                provider_transaction_id="t1",
                date=date(2026, 1, 10),
                amount=Decimal("-50.00"),
                description="iFood pedido",
            ),
            ProviderTransaction(
                provider_transaction_id="t2",
                date=date(2026, 1, 20),
                amount=Decimal("3000.00"),
                description="Salário ACME",
            ),
        ]
    }
    return FakeFinancialDataAdapter(accounts=accounts, transactions=txs)


def _connect_and_sync(client: TestClient, headers: dict[str, str]) -> None:
    client.post(
        "/connections/register",
        headers=headers,
        json={"provider_item_id": "item-f6", "institution_name": "Banco X"},
    )
    # pega o id da conexão e sincroniza
    conns = client.get("/connections", headers=headers).json()
    client.post(f"/connections/{conns[0]['id']}/sync", headers=headers)


def test_accounts_require_auth(client: TestClient) -> None:
    assert client.get("/accounts").status_code == 401
    assert client.get("/transactions").status_code == 401


def test_list_accounts_with_consolidated_balance(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        _connect_and_sync(client, headers)
        resp = client.get("/accounts", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["accounts"]) == 2
    # RN-02: total exclui cartão de crédito
    assert body["summary"]["total"] == "1000.00"
    assert body["summary"]["credit_card"] == "-200.00"


def test_list_transactions_paginated(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        _connect_and_sync(client, headers)
        resp = client.get("/transactions?page=1&page_size=1", headers=headers)
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    # ordenado por data desc → salário (jan/20) primeiro
    assert body["items"][0]["description"] == "Salário ACME"
    assert body["items"][0]["direction"] == "in"


def test_filter_transactions_by_text(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        _connect_and_sync(client, headers)
        resp = client.get("/transactions?q=ifood", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["description"] == "iFood pedido"
    assert body["items"][0]["direction"] == "out"


def test_transactions_never_expose_raw(client: TestClient) -> None:
    headers = _auth(client)
    with _override_adapter(_fake()):
        _connect_and_sync(client, headers)
        resp = client.get("/transactions", headers=headers)
    assert "raw" not in resp.text


def _fake_with_transfers() -> FakeFinancialDataAdapter:
    account = ProviderAccount(
        provider_account_id="chk", type="checking", name="C",
        currency="BRL", balance=Decimal("100.00"),
    )
    txs = {
        "chk": [
            ProviderTransaction(
                provider_transaction_id="compra", date=date(2026, 1, 10),
                amount=Decimal("-50.00"), description="Mercado",
                provider_category="Groceries",
            ),
            ProviderTransaction(  # investimento (Rende Fácil)
                provider_transaction_id="rf", date=date(2026, 1, 11),
                amount=Decimal("-300.00"), description="RENDE FACIL",
                provider_category="Automatic investment",
            ),
            ProviderTransaction(  # transferência entre contas próprias
                provider_transaction_id="self", date=date(2026, 1, 12),
                amount=Decimal("-200.00"), description="Para mim mesmo",
                provider_category="Same person transfer",
            ),
        ]
    }
    return FakeFinancialDataAdapter(accounts=[account], transactions=txs)


def test_exclude_transfers_hides_internal_movements(client: TestClient) -> None:
    headers = _auth(client, email="f6inv@e.com")
    with _override_adapter(_fake_with_transfers()):
        _connect_and_sync(client, headers)
        full = client.get("/transactions", headers=headers).json()
        filtered = client.get(
            "/transactions?exclude_transfers=true", headers=headers
        ).json()
    assert full["total"] == 3  # Mercado + Rende Fácil + transf. própria
    # com filtro: só o gasto real (Mercado); investimento e transf. própria somem
    assert filtered["total"] == 1
    assert filtered["items"][0]["description"] == "Mercado"
