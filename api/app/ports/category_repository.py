"""Port de leitura de categorias."""

from typing import Protocol
from uuid import UUID

from app.domain.category import Category


class CategoryRepository(Protocol):
    def list_system(self) -> list[Category]:
        """Categorias de sistema (seed)."""
        ...

    def list_for_user(self, user_id: UUID) -> list[Category]:
        """Categorias visíveis ao usuário: do sistema + as próprias."""
        ...
