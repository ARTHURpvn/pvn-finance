"""Adapter SQLAlchemy do CategoryRepository."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.category import Category, CategoryKind
from app.infrastructure.models import CategoryModel


class SqlCategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            kind=CategoryKind(model.kind),
            is_system=model.is_system,
            user_id=model.user_id,
            parent_id=model.parent_id,
        )

    def list_system(self) -> list[Category]:
        stmt = select(CategoryModel).where(CategoryModel.is_system.is_(True))
        return [self._to_domain(m) for m in self._session.scalars(stmt)]

    def list_for_user(self, user_id: UUID) -> list[Category]:
        stmt = select(CategoryModel).where(
            or_(
                CategoryModel.is_system.is_(True),
                CategoryModel.user_id == user_id,
            )
        )
        return [self._to_domain(m) for m in self._session.scalars(stmt)]
