"""Rota privada de exemplo — prova o escopo por usuário autenticado (NFR-002)."""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.api.schemas import UserResponse

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )
