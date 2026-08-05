"""Configurações do usuário — credenciais Pluggy (multi-tenant).

O client_secret é cifrado em repouso e NUNCA retornado pela API. Ao salvar,
validamos as credenciais contra o Pluggy (/auth) para dar feedback imediato."""

import httpx
from fastapi import APIRouter, status

from app.api.deps import ApiRateLimit, CurrentUser, SessionDep
from app.api.errors import api_error
from app.api.schemas import (
    PluggyCredentialInput,
    PluggyCredentialStatusResponse,
)
from app.bootstrap import get_vault
from app.infrastructure.pluggy_credential_repository import (
    SqlPluggyCredentialRepository,
)

router = APIRouter(
    prefix="/settings/pluggy", tags=["settings"], dependencies=[ApiRateLimit]
)


def _repo(session: SessionDep) -> SqlPluggyCredentialRepository:
    return SqlPluggyCredentialRepository(session, get_vault())


def _validate_with_pluggy(client_id: str, client_secret: str, base_url: str) -> None:
    """Confere as credenciais no Pluggy (/auth). Rejeita credencial inválida;
    erro de rede NÃO bloqueia o salvamento (a app tenta de novo depois)."""
    try:
        resp = httpx.post(
            f"{base_url.rstrip('/')}/auth",
            json={"clientId": client_id, "clientSecret": client_secret},
            timeout=15.0,
        )
    except httpx.HTTPError:
        return  # rede indisponível: salva mesmo assim
    if resp.status_code >= 400:
        raise api_error(
            code="invalid_pluggy_credentials",
            message="Credenciais Pluggy inválidas (o Pluggy recusou o clientId/clientSecret).",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("", response_model=PluggyCredentialStatusResponse)
def get_pluggy(
    current_user: CurrentUser, session: SessionDep
) -> PluggyCredentialStatusResponse:
    s = _repo(session).status(current_user.id)
    return PluggyCredentialStatusResponse(
        configured=s.configured, client_id=s.client_id, base_url=s.base_url
    )


@router.put("", response_model=PluggyCredentialStatusResponse)
def set_pluggy(
    body: PluggyCredentialInput, current_user: CurrentUser, session: SessionDep
) -> PluggyCredentialStatusResponse:
    base_url = body.base_url or "https://api.pluggy.ai"
    _validate_with_pluggy(body.client_id, body.client_secret, base_url)
    repo = _repo(session)
    repo.upsert(
        user_id=current_user.id,
        client_id=body.client_id,
        client_secret=body.client_secret,
        base_url=base_url,
    )
    s = repo.status(current_user.id)
    return PluggyCredentialStatusResponse(
        configured=s.configured, client_id=s.client_id, base_url=s.base_url
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_pluggy(current_user: CurrentUser, session: SessionDep) -> None:
    _repo(session).delete(current_user.id)
