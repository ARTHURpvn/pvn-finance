"""Rotas de autenticação: registro, login e refresh de token."""

from fastapi import APIRouter, Depends, status

from app.api.deps import AuthServiceDep
from app.api.errors import api_error
from app.api.rate_limit import auth_rate_limit
from app.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.application.auth_service import EmailAlreadyExists, InvalidCredentials

router = APIRouter(
    prefix="/auth", tags=["auth"], dependencies=[Depends(auth_rate_limit)]
)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(body: RegisterRequest, service: AuthServiceDep) -> UserResponse:
    try:
        user = service.register(email=body.email, password=body.password)
    except EmailAlreadyExists as exc:
        raise api_error(
            code="email_taken",
            message="Já existe uma conta com este email",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc
    return UserResponse(id=user.id, email=user.email, created_at=user.created_at)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    try:
        pair = service.authenticate(email=body.email, password=body.password)
    except InvalidCredentials as exc:
        raise api_error(
            code="invalid_credentials",
            message="Email ou senha inválidos",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    return TokenResponse(
        access_token=pair.access_token, refresh_token=pair.refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, service: AuthServiceDep) -> TokenResponse:
    try:
        pair = service.refresh(body.refresh_token)
    except InvalidCredentials as exc:
        raise api_error(
            code="invalid_token",
            message="Refresh token inválido ou expirado",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    return TokenResponse(
        access_token=pair.access_token, refresh_token=pair.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, service: AuthServiceDep) -> None:
    """Revoga a família do refresh token (invalida a sessão). Idempotente."""
    service.logout(body.refresh_token)
