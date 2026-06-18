"""Rotas de categorias (F7 / FR-014)."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.api.schemas import CategoryCreate, CategoryResponse
from app.domain.category import Category, CategoryKind
from app.infrastructure.category_repository import SqlCategoryRepository

router = APIRouter(prefix="/categories", tags=["categories"])


def _to_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        name=category.name,
        kind=category.kind.value,
        is_system=category.is_system,
        parent_id=category.parent_id,
    )


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    current_user: CurrentUser, session: SessionDep
) -> list[CategoryResponse]:
    repo = SqlCategoryRepository(session)
    return [_to_response(c) for c in repo.list_for_user(current_user.id)]


@router.post(
    "", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category(
    body: CategoryCreate, current_user: CurrentUser, session: SessionDep
) -> CategoryResponse:
    repo = SqlCategoryRepository(session)
    category = repo.add(
        user_id=current_user.id,
        name=body.name,
        kind=CategoryKind(body.kind),
        parent_id=body.parent_id,
    )
    return _to_response(category)
