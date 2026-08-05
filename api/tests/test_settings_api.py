"""Credenciais Pluggy por usuário (multi-tenant) — endpoints /settings/pluggy.

O segredo é cifrado e nunca retornado; a validação contra o Pluggy é
neutralizada aqui (não bate na rede)."""

import pytest
from fastapi.testclient import TestClient

from app.api import settings as settings_module


def _auth(client: TestClient, email: str = "pluggycred@e.com") -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "supersecret1"})
    resp = client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(autouse=True)
def _no_network_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    # não valida contra a rede nos testes
    monkeypatch.setattr(settings_module, "_validate_with_pluggy", lambda *a, **k: None)


def test_status_starts_unconfigured(client: TestClient) -> None:
    headers = _auth(client)
    body = client.get("/settings/pluggy", headers=headers).json()
    assert body == {"configured": False, "client_id": None, "base_url": None}


def test_put_stores_and_never_leaks_secret(client: TestClient) -> None:
    headers = _auth(client)
    resp = client.put(
        "/settings/pluggy",
        headers=headers,
        json={"client_id": "cid-123", "client_secret": "sec-xyz"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["client_id"] == "cid-123"
    assert body["base_url"] == "https://api.pluggy.ai"
    # o segredo NUNCA aparece na resposta
    assert "sec-xyz" not in resp.text
    assert "client_secret" not in body

    # GET também não vaza o segredo
    got = client.get("/settings/pluggy", headers=headers)
    assert "sec-xyz" not in got.text
    assert got.json()["configured"] is True


def test_delete_removes_credentials(client: TestClient) -> None:
    headers = _auth(client)
    client.put(
        "/settings/pluggy",
        headers=headers,
        json={"client_id": "cid", "client_secret": "sec"},
    )
    assert client.delete("/settings/pluggy", headers=headers).status_code == 204
    assert client.get("/settings/pluggy", headers=headers).json()["configured"] is False


def test_credentials_are_isolated_per_user(client: TestClient) -> None:
    a = _auth(client, "userA@e.com")
    b = _auth(client, "userB@e.com")
    client.put(
        "/settings/pluggy",
        headers=a,
        json={"client_id": "cid-A", "client_secret": "sec-A"},
    )
    # B não vê a credencial de A
    assert client.get("/settings/pluggy", headers=b).json()["configured"] is False
    assert client.get("/settings/pluggy", headers=a).json()["client_id"] == "cid-A"
