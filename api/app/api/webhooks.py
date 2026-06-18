"""Receptor de webhook do Pluggy (F9 / FR-023). Sem JWT (rota /webhooks/*).

Valida assinatura HMAC (se configurada), identifica a conexão pelo itemId
e dispara sync incremental em background (resposta rápida)."""

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
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.db import get_sessionmaker
from app.logging_config import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger("consolida.webhook")


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
                code="invalid_signature",
                message="Assinatura inválida",
                status_code=401,
            )

    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise api_error(
            code="invalid_payload", message="Payload inválido", status_code=400
        ) from exc

    item_id = payload.get("itemId") or (payload.get("item") or {}).get("id")
    event = payload.get("event")
    if not item_id:
        return {"received": True, "synced": False}

    with get_sessionmaker()() as session:
        connection = SqlConnectionRepository(session).get_by_provider_item(
            "pluggy", str(item_id)
        )

    if connection is None:
        logger.info("webhook.unknown_item event=%s", event)
        return {"received": True, "synced": False}

    background.add_task(_run_sync, connection.id, connection.user_id)
    logger.info("webhook.accepted event=%s connection_id=%s", event, connection.id)
    return {"received": True, "synced": True}
