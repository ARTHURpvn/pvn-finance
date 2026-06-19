"""Receptor de webhook do Pluggy (F9 / FR-023). Sem JWT (rota /webhooks/*).

Responde rápido (< 5s) e processa em background. Valida assinatura HMAC se
PLUGGY_WEBHOOK_SECRET estiver configurado. Eventos tratados:
- item/created, item/updated, transactions/* → sync incremental
- item/error, item/login_error            → marca conexão como erro
Identifica a conexão pelo itemId; ignora itens desconhecidos (200)."""

import hashlib
import hmac
import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Header, Request

from app.api.errors import api_error
from app.application.sync_service import SyncFailed
from app.bootstrap import build_sync_service, make_financial_adapter
from app.config import get_settings
from app.domain.connection import ConnectionStatus
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.db import get_sessionmaker
from app.logging_config import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger("consolida.webhook")

# Eventos que indicam dados novos prontos → disparar sync.
_SYNC_EVENTS = {
    "item/created",
    "item/updated",
    "item/login_succeeded",
    "transactions/created",
    "transactions/updated",
}
# Eventos de falha → marcar conexão como erro.
_ERROR_EVENTS = {"item/error", "item/login_error"}


def _valid_signature(raw: bytes, signature: str | None, secret: str) -> bool:
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return signature is not None and hmac.compare_digest(expected, signature)


def _run_sync(connection_id: UUID, user_id: UUID) -> None:
    adapter = make_financial_adapter()
    if adapter is None:
        logger.warning("webhook.sync_skipped reason=adapter_unconfigured")
        return
    with get_sessionmaker()() as session:
        try:
            build_sync_service(session, adapter).sync(
                connection_id=connection_id, user_id=user_id
            )
            logger.info("webhook.sync_ok connection_id=%s", connection_id)
        except SyncFailed:
            logger.warning("webhook.sync_failed connection_id=%s", connection_id)


def _mark_error(connection_id: UUID) -> None:
    with get_sessionmaker()() as session:
        SqlConnectionRepository(session).set_status(
            connection_id, ConnectionStatus.ERRO
        )
    logger.info("webhook.item_error connection_id=%s", connection_id)


@router.post("/pluggy")
async def pluggy_webhook(
    request: Request,
    background: BackgroundTasks,
    x_webhook_signature: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    raw = await request.body()
    settings = get_settings()

    if settings.pluggy_webhook_secret:
        if not _valid_signature(raw, x_webhook_signature, settings.pluggy_webhook_secret):
            raise api_error(
                code="invalid_signature", message="Assinatura inválida", status_code=401
            )

    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise api_error(
            code="invalid_payload", message="Payload inválido", status_code=400
        ) from exc

    event = payload.get("event")
    event_id = payload.get("eventId")
    item_id = payload.get("itemId") or (payload.get("item") or {}).get("id")
    logger.info("webhook.received event=%s event_id=%s", event, event_id)

    if not item_id:
        return {"received": True, "handled": False}

    with get_sessionmaker()() as session:
        connection = SqlConnectionRepository(session).get_by_provider_item(
            "pluggy", str(item_id)
        )

    if connection is None:
        # Item ainda não registrado por nenhum usuário (ex.: item/created antes
        # do front registrar a conexão). Aceita e ignora.
        logger.info("webhook.unknown_item event=%s", event)
        return {"received": True, "handled": False}

    if event in _ERROR_EVENTS:
        background.add_task(_mark_error, connection.id)
    elif event in _SYNC_EVENTS:
        background.add_task(_run_sync, connection.id, connection.user_id)
    else:
        return {"received": True, "handled": False}

    return {"received": True, "handled": True}
