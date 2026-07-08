"""Ports de segurança: hash de senha e emissão/validação de tokens.

A aplicação depende destas interfaces; as implementações concretas
(Argon2, JWT) vivem em infrastructure."""

from typing import Protocol


class TokenError(Exception):
    """Token inválido, expirado ou de tipo inesperado."""


class PasswordHasher(Protocol):
    def hash(self, plain: str) -> str: ...
    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenService(Protocol):
    def create_access(self, subject: str) -> str: ...
    def create_refresh(self, subject: str, *, jti: str, family_id: str) -> str: ...
    def decode(self, token: str, *, expected_type: str) -> dict[str, str]:
        """Valida assinatura/expiração/tipo. Levanta TokenError se inválido."""
        ...
