"""Serviço de autenticação — registro, login, rotação/revogação de refresh."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.user import User
from app.ports.refresh_token_repository import RefreshTokenRepository
from app.ports.security import PasswordHasher, TokenError, TokenService
from app.ports.user_repository import UserRepository

# Hash dummy (Argon2) computado uma vez por processo, usado para dar ao login
# de um email inexistente o MESMO custo de tempo de um email existente —
# evita enumeração de usuários por timing.
_dummy_hash: str | None = None


def _get_dummy_hash(hasher: PasswordHasher) -> str:
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hasher.hash("constant-time-login-placeholder")
    return _dummy_hash


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
        refresh_tokens: RefreshTokenRepository,
        *,
        refresh_ttl_minutes: int,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._refresh_tokens = refresh_tokens
        self._refresh_ttl_minutes = refresh_ttl_minutes

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
        if record is None:
            # Consome o mesmo tempo do caminho válido (constant-time) e falha.
            self._hasher.verify(password, _get_dummy_hash(self._hasher))
            raise InvalidCredentials
        if not self._hasher.verify(password, record.password_hash):
            raise InvalidCredentials
        return self._issue_pair(record.id, record.to_public(), family_id=uuid4())

    def refresh(self, refresh_token: str) -> TokenPair:
        """Rotação: valida o refresh, revoga-o e emite um par novo. Reuso de um
        token já rotacionado revoga a família inteira (detecção de replay)."""
        try:
            payload = self._tokens.decode(refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise InvalidCredentials from exc
        try:
            jti = UUID(payload["jti"])
            family_id = UUID(payload["fid"])
            user_id = UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise InvalidCredentials from exc

        stored = self._refresh_tokens.get(jti)
        if stored is None:
            raise InvalidCredentials
        if stored.revoked:
            # Token já rotacionado sendo reusado → possível roubo: derruba tudo.
            self._refresh_tokens.revoke_family(family_id)
            raise InvalidCredentials

        record = self._users.get_by_id(user_id)
        if record is None:
            raise InvalidCredentials

        self._refresh_tokens.revoke(jti)  # rotação: o token usado morre aqui
        return self._issue_pair(user_id, record.to_public(), family_id=family_id)

    def logout(self, refresh_token: str) -> None:
        """Revoga a família do refresh (idempotente: token inválido é ignorado)."""
        try:
            payload = self._tokens.decode(refresh_token, expected_type="refresh")
            self._refresh_tokens.revoke_family(UUID(payload["fid"]))
        except (TokenError, KeyError, ValueError):
            return

    def _issue_pair(self, user_id: UUID, user: User, *, family_id: UUID) -> TokenPair:
        subject = str(user_id)
        jti = uuid4()
        expires_at = datetime.now(UTC) + timedelta(minutes=self._refresh_ttl_minutes)
        self._refresh_tokens.add(
            jti=jti, user_id=user_id, family_id=family_id, expires_at=expires_at
        )
        return TokenPair(
            access_token=self._tokens.create_access(subject),
            refresh_token=self._tokens.create_refresh(
                subject, jti=str(jti), family_id=str(family_id)
            ),
            user=user,
        )
