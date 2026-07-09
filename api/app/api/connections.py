"""Rotas de conexões bancárias (F5). Todas escopadas por user_id."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import (
    ApiRateLimit,
    ConnectionServiceDep,
    CurrentUser,
    SyncServiceDep,
)
from app.api.errors import api_error
from app.api.schemas import (
    ConnectionResponse,
    ConnectTokenResponse,
    RegisterConnectionRequest,
    SyncResultResponse,
)
from app.application.connection_service import (
    ConnectionAlreadyExists,
    ConnectionNotFound,
)
from app.application.sync_service import SyncFailed
from app.domain.connection import Connection

router = APIRouter(prefix="/connections", tags=["connections"])


def _to_response(connection: Connection) -> ConnectionResponse:
    return ConnectionResponse(
        id=connection.id,
        provider=connection.provider,
        institution_name=connection.institution_name,
        status=connection.status.value,
        consent_expires_at=connection.consent_expires_at,
        last_sync_at=connection.last_sync_at,
    )


@router.post("", response_model=ConnectTokenResponse, status_code=status.HTTP_201_CREATED)
def start_connection(
    current_user: CurrentUser, service: ConnectionServiceDep
) -> ConnectTokenResponse:
    """FR-003: inicia conexão, retornando o token do widget."""
    return ConnectTokenResponse(
        connect_token=service.create_connect_token(current_user.id)
    )


@router.post(
    "/register",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_connection(
    body: RegisterConnectionRequest,
    current_user: CurrentUser,
    service: ConnectionServiceDep,
) -> ConnectionResponse:
    try:
        connection = service.register(
            user_id=current_user.id,
            provider_item_id=body.provider_item_id,
            institution_name=body.institution_name,
        )
    except ConnectionAlreadyExists as exc:
        raise api_error(
            code="connection_exists",
            message="Conexão já registrada",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc
    return _to_response(connection)


@router.get("", response_model=list[ConnectionResponse])
def list_connections(
    current_user: CurrentUser, service: ConnectionServiceDep
) -> list[ConnectionResponse]:
    return [_to_response(c) for c in service.list(current_user.id)]


@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: UUID, current_user: CurrentUser, service: ConnectionServiceDep
) -> ConnectionResponse:
    try:
        connection = service.get(connection_id, current_user.id)
    except ConnectionNotFound as exc:
        raise _not_found() from exc
    return _to_response(connection)


@router.post(
    "/{connection_id}/sync",
    response_model=SyncResultResponse,
    dependencies=[ApiRateLimit],
)
def sync_connection(
    connection_id: UUID, current_user: CurrentUser, service: SyncServiceDep
) -> SyncResultResponse:
    from app.application.sync_service import ConnectionNotFound as SyncConnNotFound

    try:
        result = service.sync(connection_id=connection_id, user_id=current_user.id)
    except SyncConnNotFound as exc:
        raise _not_found() from exc
    except SyncFailed as exc:
        raise api_error(
            code="sync_failed",
            message="Falha ao sincronizar com o agregador",
            status_code=status.HTTP_502_BAD_GATEWAY,
        ) from exc
    return SyncResultResponse(status=result.status, imported=result.imported)


@router.post("/{connection_id}/reauth", response_model=ConnectTokenResponse)
def reauth_connection(
    connection_id: UUID, current_user: CurrentUser, service: ConnectionServiceDep
) -> ConnectTokenResponse:
    try:
        token = service.reauth_token(connection_id, current_user.id)
    except ConnectionNotFound as exc:
        raise _not_found() from exc
    return ConnectTokenResponse(connect_token=token)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: UUID, current_user: CurrentUser, service: ConnectionServiceDep
) -> None:
    try:
        service.delete(connection_id, current_user.id)
    except ConnectionNotFound as exc:
        raise _not_found() from exc


def _not_found():
    return api_error(
        code="connection_not_found",
        message="Conexão não encontrada",
        status_code=status.HTTP_404_NOT_FOUND,
    )
