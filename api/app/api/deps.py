"""Dependências FastAPI: sessão, serviço de auth e usuário autenticado."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.application.auth_service import AuthService
from app.domain.user import User
from app.infrastructure.db import get_session
from app.infrastructure.security import Argon2PasswordHasher, JwtTokenService
from app.infrastructure.user_repository import SqlUserRepository
from app.ports.security import TokenError

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(
        users=SqlUserRepository(session),
        hasher=Argon2PasswordHasher(),
        tokens=JwtTokenService(),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = api_error(
        code="unauthorized", message="Não autenticado", status_code=401
    )
    if credentials is None:
        raise unauthorized
    tokens = JwtTokenService()
    try:
        payload = tokens.decode(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise unauthorized from exc
    record = SqlUserRepository(session).get_by_id(UUID(payload["sub"]))
    if record is None:
        raise unauthorized
    return record.to_public()


CurrentUser = Annotated[User, Depends(get_current_user)]
