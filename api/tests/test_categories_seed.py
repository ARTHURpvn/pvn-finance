"""Seed de categorias de sistema aplicado pela migration (integração)."""

from sqlalchemy.orm import Session

from app.domain.category import FALLBACK_CATEGORY_NAME, SYSTEM_CATEGORIES
from app.infrastructure.category_repository import SqlCategoryRepository


def test_system_categories_are_seeded(db_session: Session) -> None:
    repo = SqlCategoryRepository(db_session)
    system = repo.list_system()

    assert len(system) == len(SYSTEM_CATEGORIES)
    names = {c.name for c in system}
    assert FALLBACK_CATEGORY_NAME in names
    assert all(c.is_system and c.user_id is None for c in system)
