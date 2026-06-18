"""API do dashboard (F8) — agregações com dados semeados via sync (fake)."""

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


def _auth(client: TestClient, email: str = "f8@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _seed(client: TestClient, headers: dict[str, str]) -> None:
    pa = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="CC",
        currency="BRL",
        balance=Decimal("0"),
    )
    txs = [
        ProviderTransaction(
            provider_transaction_id="t1",
            date=date(2026, 1, 5),
            amount=Decimal("5000.00"),
            description="Salário",
        ),
        ProviderTransaction(
            provider_transaction_id="t2",
            date=date(2026, 1, 10),
            amount=Decimal("-200.00"),
            description="Mercado",
        ),
        ProviderTransaction(
            provider_transaction_id="t3",
            date=date(2026, 2, 10),
            amount=Decimal("-300.00"),
            description="Aluguel",
        ),
    ]
    fake = FakeFinancialDataAdapter(accounts=[pa], transactions={"acc-1": txs})
    with _override_adapter(fake):
        client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "i", "institution_name": "B"},
        )
        cid = client.get("/connections", headers=headers).json()[0]["id"]
        client.post(f"/connections/{cid}/sync", headers=headers)


def test_dashboard_requires_auth(client: TestClient) -> None:
    assert client.get("/dashboard/summary").status_code == 401


def test_summary(client: TestClient) -> None:
    headers = _auth(client)
    _seed(client, headers)
    body = client.get("/dashboard/summary", headers=headers).json()
    assert body["received"] == "5000.00"
    assert body["spent"] == "500.00"  # 200 + 300
    assert body["net"] == "4500.00"


def test_summary_with_date_filter(client: TestClient) -> None:
    headers = _auth(client)
    _seed(client, headers)
    body = client.get(
        "/dashboard/summary?from=2026-02-01&to=2026-02-28", headers=headers
    ).json()
    assert body["received"] == "0"
    assert body["spent"] == "300.00"


def test_by_category(client: TestClient) -> None:
    headers = _auth(client)
    _seed(client, headers)
    rows = client.get("/dashboard/by-category", headers=headers).json()
    # só despesas; sem regra → "Outros" (fallback) ou "Sem categoria"
    total = sum(Decimal(r["total"]) for r in rows)
    assert total == Decimal("500.00")


def test_timeline_monthly(client: TestClient) -> None:
    headers = _auth(client)
    _seed(client, headers)
    rows = client.get("/dashboard/timeline", headers=headers).json()
    by_month = {r["month"]: r for r in rows}
    assert by_month["2026-01"]["in"] == "5000.00"
    assert by_month["2026-01"]["out"] == "200.00"
    assert by_month["2026-02"]["out"] == "300.00"
