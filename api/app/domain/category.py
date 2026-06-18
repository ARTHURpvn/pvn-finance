"""Categoria — entidade de domínio + taxonomia de sistema (seed)."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class CategoryKind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


#: Nome da categoria de fallback (ADR-004): usada quando não há regra do
#: usuário nem categoria do agregador.
FALLBACK_CATEGORY_NAME = "Outros"


@dataclass(frozen=True, slots=True)
class Category:
    """Categoria. ``user_id`` nulo + ``is_system=True`` = categoria do sistema."""

    id: UUID
    name: str
    kind: CategoryKind
    is_system: bool
    user_id: UUID | None = None
    parent_id: UUID | None = None


#: Taxonomia de categorias de sistema semeada na migration (F3).
SYSTEM_CATEGORIES: tuple[tuple[str, CategoryKind], ...] = (
    ("Alimentação", CategoryKind.EXPENSE),
    ("Mercado", CategoryKind.EXPENSE),
    ("Transporte", CategoryKind.EXPENSE),
    ("Moradia", CategoryKind.EXPENSE),
    ("Saúde", CategoryKind.EXPENSE),
    ("Educação", CategoryKind.EXPENSE),
    ("Lazer", CategoryKind.EXPENSE),
    ("Compras", CategoryKind.EXPENSE),
    ("Serviços", CategoryKind.EXPENSE),
    ("Assinaturas", CategoryKind.EXPENSE),
    (FALLBACK_CATEGORY_NAME, CategoryKind.EXPENSE),
    ("Salário", CategoryKind.INCOME),
    ("Rendimentos", CategoryKind.INCOME),
    ("Transferências recebidas", CategoryKind.INCOME),
    ("Transferência entre contas", CategoryKind.TRANSFER),
)
