"""Cofre de credenciais (ADR-005)."""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.infrastructure.vault import CredentialVault


def test_encrypt_then_decrypt_roundtrip() -> None:
    vault = CredentialVault(Fernet.generate_key().decode())
    secret = "pluggy-item-secret-xyz"

    token = vault.encrypt(secret)

    assert token != secret.encode()  # ciphertext != plaintext
    assert secret.encode() not in token  # segredo não aparece em claro
    assert vault.decrypt(token) == secret


def test_decrypt_with_wrong_key_fails() -> None:
    token = CredentialVault(Fernet.generate_key().decode()).encrypt("segredo")
    other_vault = CredentialVault(Fernet.generate_key().decode())

    with pytest.raises(InvalidToken):
        other_vault.decrypt(token)


def test_invalid_key_raises() -> None:
    with pytest.raises(ValueError):
        CredentialVault("not-a-valid-fernet-key")
