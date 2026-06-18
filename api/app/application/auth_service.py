"""Serviço de autenticação — orquestra registro e login sobre os ports."""

from dataclasses import dataclass
from uuid import UUID

from app.domain.user import User
from app.ports.security import PasswordHasher, TokenError, TokenService
from app.ports.user_repository import UserRepository


class EmailAlreadyExists(Exception):
    """Já existe usuário com o email informado."""


class InvalidCredentials(Exception):
    """Credenciais inválidas ou token de refresh inválido."""


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    user: User


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    def register(self, *, email: str, password: str) -> User:
        normalized = email.strip().lower()
        if self._users.get_by_email(normalized) is not None:
            raise EmailAlreadyExists
        record = self._users.add(
            email=normalized, password_hash=self._hasher.hash(password)
        )
        return record.to_public()

    def authenticate(self, *, email: str, password: str) -> TokenPair:
        record = self._users.get_by_email(email.strip().lower())
        # Verifica a senha mesmo sem usuário não é necessário aqui; a resposta
        # 401 é idêntica nos dois casos (evita enumeração de usuários).
        if record is None or not self._hasher.verify(password, record.password_hash):
            raise InvalidCredentials
        subject = str(record.id)
        return TokenPair(
            access_token=self._tokens.create_access(subject),
            refresh_token=self._tokens.create_refresh(subject),
            user=record.to_public(),
        )

    def refresh(self, refresh_token: str) -> str:
        try:
            payload = self._tokens.decode(refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise InvalidCredentials from exc
        subject = payload["sub"]
        if self._users.get_by_id(UUID(subject)) is None:
            raise InvalidCredentials
        return self._tokens.create_access(subject)
