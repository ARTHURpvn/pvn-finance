"""Port de categorias."""

from typing import Protocol
from uuid import UUID

from app.domain.category import Category, CategoryKind


class CategoryRepository(Protocol):
    def list_system(self) -> list[Category]:
        """Categorias de sistema (seed)."""
        ...

    def list_for_user(self, user_id: UUID) -> list[Category]:
        """Categorias visíveis ao usuário: do sistema + as próprias."""
        ...

    def get_for_user(self, category_id: UUID, user_id: UUID) -> Category | None:
        """Categoria acessível ao usuário (sistema ou própria)."""
        ...

    def add(
        self,
        *,
        user_id: UUID,
        name: str,
        kind: CategoryKind,
        parent_id: UUID | None = None,
    ) -> Category:
        """Cria categoria do usuário."""
        ...
