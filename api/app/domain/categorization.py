"""Motor de categorização em camadas (ADR-004).

Precedência: 1) regra do usuário (por prioridade) → 2) categoria do
agregador (match por nome) → 3) fallback ("Outros")."""

from collections.abc import Iterable
from uuid import UUID

from app.domain.category import Category
from app.domain.rule import Rule


def categorize(
    *,
    description: str,
    provider_category: str | None,
    rules: Iterable[Rule],
    categories: Iterable[Category],
    fallback_id: UUID | None,
) -> UUID | None:
    """Resolve a categoria de uma transação seguindo a precedência do ADR-004.

    ``rules`` são aplicadas por ``priority`` crescente (menor = maior
    precedência); a primeira que casar vence."""
    for rule in sorted(rules, key=lambda r: r.priority):
        if rule.matches(description):
            return rule.category_id

    if provider_category:
        key = provider_category.strip().lower()
        for category in categories:
            if category.name.lower() == key:
                return category.id

    return fallback_id
