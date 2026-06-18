"""Rota privada do usuário autenticado: dados e exclusão de conta (LGPD)."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.api.schemas import UserResponse
from app.infrastructure.user_repository import SqlUserRepository

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user: CurrentUser, session: SessionDep) -> None:
    """FR-006 / NFR-003: exclui o usuário e TODOS os seus dados (cascata)."""
    SqlUserRepository(session).delete(current_user.id)
