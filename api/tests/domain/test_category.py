"""Taxonomia de categorias de sistema (seed)."""

from app.domain.category import (
    FALLBACK_CATEGORY_NAME,
    SYSTEM_CATEGORIES,
    CategoryKind,
)


def test_fallback_category_present_as_expense() -> None:
    assert (FALLBACK_CATEGORY_NAME, CategoryKind.EXPENSE) in SYSTEM_CATEGORIES


def test_all_kinds_represented() -> None:
    kinds = {kind for _, kind in SYSTEM_CATEGORIES}
    assert kinds == {CategoryKind.INCOME, CategoryKind.EXPENSE, CategoryKind.TRANSFER}


def test_taxonomy_is_non_trivial() -> None:
    assert len(SYSTEM_CATEGORIES) >= 10
