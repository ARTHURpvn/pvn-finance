"""F10 — exclusão total de dados (LGPD) e rate limiting de /auth/*."""

from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.adapters.fake import FakeFinancialDataAdapter
from app.api.deps import get_financial_adapter
from app.api.rate_limit import get_auth_limiter
from app.infrastructure.db import get_sessionmaker
from app.infrastructure.models import (
    AccountModel,
    ConnectionModel,
    TransactionModel,
    UserModel,
)
from app.main import app
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


@contextmanager
def _override_adapter(adapter):
    app.dependency_overrides[get_financial_adapter] = lambda: adapter
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_financial_adapter, None)


def _auth(client: TestClient, email: str) -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _seed_data(client: TestClient, headers: dict[str, str]) -> None:
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
        amount=Decimal("-10"),
        description="x",
    )
    fake = FakeFinancialDataAdapter(accounts=[pa], transactions={"acc-1": [pt]})
    with _override_adapter(fake):
        client.post(
            "/connections/register",
            headers=headers,
            json={"provider_item_id": "item-lgpd", "institution_name": "B"},
        )
        cid = client.get("/connections", headers=headers).json()[0]["id"]
        client.post(f"/connections/{cid}/sync", headers=headers)


def test_delete_account_removes_all_data(client: TestClient) -> None:
    headers = _auth(client, "erase@e.com")
    _seed_data(client, headers)

    resp = client.delete("/me", headers=headers)
    assert resp.status_code == 204

    # token antigo não acessa mais
    assert client.get("/me", headers=headers).status_code == 401

    # nada do usuário sobra no banco
    with get_sessionmaker()() as session:
        users = session.query(UserModel).filter_by(email="erase@e.com").count()
        conns = session.query(ConnectionModel).count()
        accs = session.query(AccountModel).count()
        txs = session.query(TransactionModel).count()
    assert users == 0
    assert conns == 0 and accs == 0 and txs == 0


def test_delete_account_requires_auth(client: TestClient) -> None:
    assert client.delete("/me").status_code == 401


def test_auth_rate_limit_returns_429_with_retry_after(client: TestClient) -> None:
    limiter = get_auth_limiter()
    limiter.clear()
    original = limiter.max_attempts
    limiter.max_attempts = 2
    try:
        # 2 permitidas, 3ª bloqueada
        client.post("/auth/login", json={"email": "a@e.com", "password": "x"})
        client.post("/auth/login", json={"email": "a@e.com", "password": "x"})
        blocked = client.post(
            "/auth/login", json={"email": "a@e.com", "password": "x"}
        )
        assert blocked.status_code == 429
        assert blocked.json()["error"]["code"] == "rate_limited"
        assert "retry-after" in {k.lower() for k in blocked.headers}
    finally:
        limiter.max_attempts = original
        limiter.clear()
