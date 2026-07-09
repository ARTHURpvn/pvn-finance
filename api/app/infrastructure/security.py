"""Implementações concretas dos ports de segurança: Argon2 + JWT (HS256).

Segredos nunca são logados. O segredo do JWT vem do ambiente (NFR-001)."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import get_settings
from app.ports.security import TokenError

_password_hash = PasswordHash.recommended()


class Argon2PasswordHasher:
    """Implementa PasswordHasher usando Argon2 (via pwdlib)."""

    def hash(self, plain: str) -> str:
        return _password_hash.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return _password_hash.verify(plain, hashed)


class JwtTokenService:
    """Implementa TokenService com JWT assinado em HS256."""

    def _create(
        self,
        subject: str,
        *,
        minutes: int,
        token_type: str,
        extra: dict[str, str] | None = None,
    ) -> str:
        settings = get_settings()
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(minutes=minutes),
            **(extra or {}),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def create_access(self, subject: str) -> str:
        return self._create(
            subject,
            minutes=get_settings().jwt_access_expire_minutes,
            token_type="access",
        )

    def create_refresh(self, subject: str, *, jti: str, family_id: str) -> str:
        return self._create(
            subject,
            minutes=get_settings().jwt_refresh_expire_minutes,
            token_type="refresh",
            extra={"jti": jti, "fid": family_id},
        )

    def decode(self, token: str, *, expected_type: str) -> dict[str, str]:
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise TokenError("token inválido ou expirado") from exc
        if payload.get("type") != expected_type:
            raise TokenError("tipo de token inesperado")
        return payload
