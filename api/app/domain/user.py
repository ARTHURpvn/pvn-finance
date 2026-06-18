"""Entidade de domínio User. Puro — sem dependências de framework/ORM.

`User` é a forma pública (nunca carrega segredo). `UserRecord` inclui o
`password_hash` e é usado apenas internamente pela autenticação.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    """Usuário em sua forma pública — sem credenciais."""

    id: UUID
    email: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class UserRecord:
    """Usuário com credencial — uso interno (autenticação). Nunca serializar."""

    id: UUID
    email: str
    password_hash: str
    created_at: datetime

    def to_public(self) -> User:
        return User(id=self.id, email=self.email, created_at=self.created_at)
