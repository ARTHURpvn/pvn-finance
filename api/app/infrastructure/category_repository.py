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

    def get_for_user(self, category_id: UUID, user_id: UUID) -> Category | None:
        """Categoria acessível ao usuário (do sistema ou própria)."""
        model = self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        if not model.is_system and model.user_id != user_id:
            return None
        return self._to_domain(model)

    def add(
        self,
        *,
        user_id: UUID,
        name: str,
        kind: CategoryKind,
        parent_id: UUID | None = None,
    ) -> Category:
        model = CategoryModel(
            user_id=user_id,
            name=name,
            kind=kind.value,
            is_system=False,
            parent_id=parent_id,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)
