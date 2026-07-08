"""Testes de integração da API de autenticação (CA-1..CA-9)."""

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, password: str):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_returns_201_without_secret(client: TestClient) -> None:
    resp = _register(client, "alice@example.com", "supersecret1")
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    _register(client, "bob@example.com", "supersecret1")
    resp = _register(client, "bob@example.com", "anotherpass1")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "email_taken"


def test_register_invalid_payload_returns_422(client: TestClient) -> None:
    short = client.post(
        "/auth/register", json={"email": "x@example.com", "password": "123"}
    )
    assert short.status_code == 422
    assert short.json()["error"]["code"] == "validation_error"

    bad_email = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "supersecret1"}
    )
    assert bad_email.status_code == 422


def test_validation_error_never_echoes_password(client: TestClient) -> None:
    secret = "123"  # curta de propósito, dispara 422
    resp = client.post(
        "/auth/register", json={"email": "leak@example.com", "password": secret}
    )
    assert resp.status_code == 422
    assert secret not in resp.text  # senha não pode vazar no corpo do erro


def test_login_returns_token_pair(client: TestClient) -> None:
    _register(client, "carol@example.com", "supersecret1")
    resp = client.post(
        "/auth/login", json={"email": "carol@example.com", "password": "supersecret1"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    _register(client, "dave@example.com", "supersecret1")
    resp = client.post(
        "/auth/login", json={"email": "dave@example.com", "password": "wrongpass1"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    resp = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "whatever12"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_me_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_me_with_valid_token_returns_user(client: TestClient) -> None:
    _register(client, "erin@example.com", "supersecret1")
    login = client.post(
        "/auth/login", json={"email": "erin@example.com", "password": "supersecret1"}
    )
    token = login.json()["access_token"]
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "erin@example.com"


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    resp = client.get("/me", headers={"Authorization": "Bearer garbage.token"})
    assert resp.status_code == 401


def test_refresh_returns_new_access_token(client: TestClient) -> None:
    _register(client, "frank@example.com", "supersecret1")
    login = client.post(
        "/auth/login", json={"email": "frank@example.com", "password": "supersecret1"}
    )
    refresh_token = login.json()["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    me = client.get("/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "frank@example.com"


def test_refresh_rejects_access_token(client: TestClient) -> None:
    _register(client, "grace@example.com", "supersecret1")
    login = client.post(
        "/auth/login", json={"email": "grace@example.com", "password": "supersecret1"}
    )
    access_token = login.json()["access_token"]
    # usar access token no refresh deve falhar (tipo errado)
    resp = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


def _login(client: TestClient, email: str) -> dict:
    _register(client, email, "supersecret1")
    return client.post(
        "/auth/login", json={"email": email, "password": "supersecret1"}
    ).json()


def test_refresh_rotates_and_old_token_is_revoked(client: TestClient) -> None:
    """Rotação: o refresh devolve um novo refresh e revoga o usado."""
    old = _login(client, "rot@example.com")["refresh_token"]

    first = client.post("/auth/refresh", json={"refresh_token": old})
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]
    assert new_refresh and new_refresh != old

    # reusar o refresh antigo (já rotacionado) → 401 (detecção de reuso)
    reused = client.post("/auth/refresh", json={"refresh_token": old})
    assert reused.status_code == 401


def test_refresh_reuse_revokes_whole_family(client: TestClient) -> None:
    """Reuso de token rotacionado derruba a família inteira (anti-replay)."""
    old = _login(client, "fam@example.com")["refresh_token"]
    new_refresh = client.post(
        "/auth/refresh", json={"refresh_token": old}
    ).json()["refresh_token"]

    # atacante reusa o antigo → dispara revogação da família
    assert client.post("/auth/refresh", json={"refresh_token": old}).status_code == 401
    # o token legítimo (novo) também foi invalidado pela detecção de reuso
    assert (
        client.post("/auth/refresh", json={"refresh_token": new_refresh}).status_code
        == 401
    )


def test_logout_revokes_refresh(client: TestClient) -> None:
    tokens = _login(client, "out@example.com")
    refresh_token = tokens["refresh_token"]

    logout = client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    # após logout, o refresh não vale mais
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401
