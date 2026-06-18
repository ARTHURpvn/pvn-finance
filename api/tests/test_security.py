"""Testes unitários das primitivas de segurança (sem banco)."""

import pytest

from app.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from app.ports.security import TokenError


def test_hash_and_verify_roundtrip() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("super-secret-123")

    assert hashed != "super-secret-123"
    assert hasher.verify("super-secret-123", hashed) is True
    assert hasher.verify("senha-errada", hashed) is False


def test_access_token_roundtrip() -> None:
    tokens = JwtTokenService()
    token = tokens.create_access("user-123")

    payload = tokens.decode(token, expected_type="access")

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_decode_rejects_wrong_token_type() -> None:
    tokens = JwtTokenService()
    refresh = tokens.create_refresh("user-123")

    with pytest.raises(TokenError):
        tokens.decode(refresh, expected_type="access")


def test_decode_rejects_tampered_token() -> None:
    tokens = JwtTokenService()

    with pytest.raises(TokenError):
        tokens.decode("not.a.valid.jwt", expected_type="access")
