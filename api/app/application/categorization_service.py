"""Serviço de categorização — aplica a precedência do ADR-004."""

from collections.abc import Callable
from uuid import UUID

from app.domain.categorization import categorize
from app.domain.category import FALLBACK_CATEGORY_NAME, CategoryKind
from app.ports.category_repository import CategoryRepository
from app.ports.repositories import RuleRepository

#: (description, provider_category) -> category_id | None
Categorizer = Callable[[str, str | None], UUID | None]


class CategorizationService:
    def __init__(
        self, *, categories: CategoryRepository, rules: RuleRepository
    ) -> None:
        self._categories = categories
        self._rules = rules

    def build_for_user(self, user_id: UUID) -> Categorizer:
        """Carrega regras+categorias do usuário uma vez e devolve um
        categorizador reutilizável (eficiente para o loop de sync)."""
        categories = self._categories.list_for_user(user_id)
        rules = self._rules.list_for_user(user_id)
        fallback_id = next(
            (
                c.id
                for c in categories
                if c.name == FALLBACK_CATEGORY_NAME and c.kind == CategoryKind.EXPENSE
            ),
            None,
        )

        def categorizer(description: str, provider_category: str | None) -> UUID | None:
            return categorize(
                description=description,
                provider_category=provider_category,
                rules=rules,
                categories=categories,
                fallback_id=fallback_id,
            )

        return categorizer
