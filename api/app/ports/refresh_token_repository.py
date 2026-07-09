"""Port de persistência de refresh tokens (rotação/revogação — F3)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    jti: UUID
    user_id: UUID
    family_id: UUID
    revoked: bool
    expires_at: datetime


class RefreshTokenRepository(Protocol):
    """Contrato de armazenamento de refresh tokens."""

    def add(
        self, *, jti: UUID, user_id: UUID, family_id: UUID, expires_at: datetime
    ) -> None: ...

    def get(self, jti: UUID) -> RefreshTokenRecord | None: ...

    def revoke(self, jti: UUID) -> None:
        """Revoga um único token (rotação)."""
        ...

    def revoke_family(self, family_id: UUID) -> None:
        """Revoga todos os tokens de uma família (logout / detecção de reuso)."""
        ...
