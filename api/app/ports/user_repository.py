"""Port de persistência de usuários. O domínio/aplicação dependem desta
interface; a implementação concreta vive em infrastructure (adapter)."""

from typing import Protocol
from uuid import UUID

from app.domain.user import UserRecord


class UserRepository(Protocol):
    """Contrato de repositório de usuários."""

    def add(self, *, email: str, password_hash: str) -> UserRecord:
        """Persiste um novo usuário e retorna o registro criado."""
        ...

    def get_by_email(self, email: str) -> UserRecord | None:
        """Busca por email (case-insensitive). None se não existir."""
        ...

    def get_by_id(self, user_id: UUID) -> UserRecord | None:
        """Busca por id. None se não existir."""
        ...
