"""Rotas de autenticação: registro, login e refresh de token."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.api.errors import api_error
from app.api.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.application.auth_service import EmailAlreadyExists, InvalidCredentials

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest, service: AuthServiceDep) -> AccessTokenResponse:
    try:
        access_token = service.refresh(body.refresh_token)
    except InvalidCredentials as exc:
        raise api_error(
            code="invalid_token",
            message="Refresh token inválido ou expirado",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc
    return AccessTokenResponse(access_token=access_token)
