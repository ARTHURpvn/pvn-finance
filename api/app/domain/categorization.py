"""Motor de categorização em camadas (ADR-004).

Precedência: 1) regra do usuário (por prioridade) → 2) categoria do
agregador (traduzida p/ a taxonomia PT) → 3) fallback ("Outros")."""

from collections.abc import Iterable
from uuid import UUID

from app.domain.category import Category
from app.domain.rule import Rule

#: Mapa da taxonomia do Pluggy (inglês/granular) → nossas categorias de
#: sistema (PT). Chaves em minúsculas. Categorias fora do mapa caem no fallback.
PROVIDER_CATEGORY_MAP: dict[str, str] = {
    # Receitas
    "salary": "Salário",
    "income": "Salário",
    "paycheck": "Salário",
    "retirement": "Rendimentos",
    "interest and earnings": "Rendimentos",
    "investment": "Rendimentos",
    "investments": "Rendimentos",
    "dividends": "Rendimentos",
    # Alimentação / mercado
    "food and drinks": "Alimentação",
    "food and drink": "Alimentação",
    "restaurants": "Alimentação",
    "delivery": "Alimentação",
    "groceries": "Mercado",
    "supermarkets": "Mercado",
    # Transporte
    "transport": "Transporte",
    "transportation": "Transporte",
    "public transportation": "Transporte",
    "fuel": "Transporte",
    "gas stations": "Transporte",
    "ride hailing": "Transporte",
    "taxi": "Transporte",
    # Moradia
    "housing": "Moradia",
    "rent": "Moradia",
    "mortgage": "Moradia",
    "condo": "Moradia",
    # Serviços / contas
    "electricity": "Serviços",
    "water": "Serviços",
    "gas": "Serviços",
    "telecommunications": "Serviços",
    "internet": "Serviços",
    "phone": "Serviços",
    "utilities": "Serviços",
    "bills": "Serviços",
    # Saúde
    "health": "Saúde",
    "healthcare": "Saúde",
    "pharmacy": "Saúde",
    "gyms and fitness centers": "Saúde",
    "gym": "Saúde",
    # Educação
    "education": "Educação",
    "courses": "Educação",
    # Lazer
    "leisure": "Lazer",
    "entertainment": "Lazer",
    "travel": "Lazer",
    "bars": "Lazer",
    # Compras
    "shopping": "Compras",
    "online shopping": "Compras",
    "clothing": "Compras",
    "electronics": "Compras",
    # Assinaturas
    "video streaming": "Assinaturas",
    "music streaming": "Assinaturas",
    "streaming": "Assinaturas",
    "subscriptions": "Assinaturas",
    "software": "Assinaturas",
    # Transferências
    "transfers": "Transferência entre contas",
    "transfer - bank slip": "Transferência entre contas",
    "transfer - pix": "Transferência entre contas",
    "same person transfer": "Transferência entre contas",
    "credit card payment": "Transferência entre contas",
    "loans and financing": "Transferência entre contas",
}


def categorize(
    *,
    description: str,
    provider_category: str | None,
    rules: Iterable[Rule],
    categories: Iterable[Category],
    fallback_id: UUID | None,
) -> UUID | None:
    """Resolve a categoria seguindo a precedência do ADR-004.

    ``rules`` são aplicadas por ``priority`` crescente (menor = maior
    precedência); a primeira que casar vence. A categoria do agregador é
    traduzida pelo PROVIDER_CATEGORY_MAP antes de casar com a taxonomia."""
    for rule in sorted(rules, key=lambda r: r.priority):
        if rule.matches(description):
            return rule.category_id

    if provider_category:
        by_name = {c.name.lower(): c.id for c in categories}
        key = provider_category.strip().lower()
        target = PROVIDER_CATEGORY_MAP.get(key, key)
        category_id = by_name.get(target.lower())
        if category_id is not None:
            return category_id

    return fallback_id
