"""Receptor de webhook do Pluggy (F9 / FR-023). Sem JWT (rota /webhooks/*).

Responde rápido (< 5s) e processa em background. O Pluggy NÃO assina o payload
(sem HMAC): a autenticação é por header secreto configurado ao criar o Webhook
na Pluggy e/ou por allowlist de IP de origem. Ao processar um evento de item,
delega ao SyncService — que faz GET /items/{id} e reconcilia o status (RN-03),
importando dados só quando o item está pronto. Idempotência por eventId.
Identifica a conexão pelo itemId; ignora itens desconhecidos (200)."""

import hmac
import json
import time
from collections import OrderedDict
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Request

from app.api.errors import api_error
from app.application.sync_service import ConnectionNotFound, SyncFailed
from app.bootstrap import build_sync_service, make_financial_adapter
from app.config import Settings, get_settings
from app.infrastructure.connection_repository import SqlConnectionRepository
from app.infrastructure.db import get_sessionmaker
from app.logging_config import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = get_logger("consolida.webhook")

#: Tamanho máximo do corpo aceito (endpoint público) — proteção contra DoS.
_MAX_BODY_BYTES = 64 * 1024

# Eventos que disparam sync/reconciliação. O SyncService lê o item e decide:
# se pronto (UPDATED) importa; se LOGIN_ERROR/MFA/consent expirado marca
# requer_reauth; se erro sistêmico marca erro. Fonte única da regra RN-03.
# `item/created` e `item/login_succeeded` são ignorados de propósito: nesses
# momentos os dados ainda estão sendo coletados (importar aqui traria 0).
_HANDLED_EVENTS = {
    "item/updated",
    "item/error",
    "item/waiting_user_input",
    "item/waiting_user_action",
    "transactions/created",
    "transactions/updated",
    "transactions/deleted",
}


class _SeenEvents:
    """Dedupe de eventId com TTL (idempotência). In-memory por processo —
    suficiente para reentregas próximas do Pluggy (até 9x); migrar para Redis
    ao escalar para múltiplos workers."""

    def __init__(self, ttl_seconds: float = 3600.0, max_size: int = 10_000) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._seen: OrderedDict[str, float] = OrderedDict()

    def seen_before(self, event_id: str, *, now: float | None = None) -> bool:
        current = now if now is not None else time.monotonic()
        self._evict(current)
        if event_id in self._seen:
            return True
        self._seen[event_id] = current
        if len(self._seen) > self._max_size:
            self._seen.popitem(last=False)
        return False

    def _evict(self, current: float) -> None:
        expired = [k for k, t in self._seen.items() if current - t > self._ttl]
        for key in expired:
            del self._seen[key]


_seen_events = _SeenEvents()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _authorized(request: Request, settings: Settings) -> bool:
    """Autentica o webhook por IP allowlist e/ou header secreto (o que estiver
    configurado). Sem nenhum dos dois, aceita apenas fora de produção."""
    allowed_ips = [
        ip.strip()
        for ip in settings.pluggy_webhook_allowed_ips.split(",")
        if ip.strip()
    ]
    if allowed_ips and _client_ip(request) not in allowed_ips:
        return False

    if settings.pluggy_webhook_secret:
        provided = request.headers.get(settings.pluggy_webhook_header)
        return provided is not None and hmac.compare_digest(
            provided, settings.pluggy_webhook_secret
        )

    # Nenhum segredo configurado: exigido em produção, tolerado em dev.
    return not allowed_ips and settings.app_env != "production"


def _run_sync(connection_id: UUID, user_id: UUID) -> None:
    adapter = make_financial_adapter()
    if adapter is None:
        logger.warning("webhook.sync_skipped reason=adapter_unconfigured")
        return
    with get_sessionmaker()() as session:
        try:
            result = build_sync_service(session, adapter).sync(
                connection_id=connection_id, user_id=user_id
            )
            logger.info(
                "webhook.sync_ok connection_id=%s status=%s imported=%s",
                connection_id,
                result.status,
                result.imported,
            )
        except ConnectionNotFound:
            logger.warning("webhook.sync_unknown connection_id=%s", connection_id)
        except SyncFailed:
            logger.warning("webhook.sync_failed connection_id=%s", connection_id)


@router.post("/pluggy")
async def pluggy_webhook(
    request: Request,
    background: BackgroundTasks,
) -> dict[str, bool]:
    settings = get_settings()

    if settings.app_env == "production" and not (
        settings.pluggy_webhook_secret or settings.pluggy_webhook_allowed_ips.strip()
    ):
        logger.error("webhook.misconfigured reason=no_auth_in_production")
        raise api_error(
            code="webhook_unconfigured",
            message="Webhook sem autenticação configurada",
            status_code=401,
        )

    if not _authorized(request, settings):
        logger.warning("webhook.unauthorized ip=%s", _client_ip(request))
        raise api_error(
            code="unauthorized", message="Não autorizado", status_code=401
        )

    content_length = request.headers.get("content-length")
    if content_length is not None and content_length.isdigit():
        if int(content_length) > _MAX_BODY_BYTES:
            raise api_error(
                code="payload_too_large", message="Payload grande", status_code=413
            )

    raw = await request.body()
    if len(raw) > _MAX_BODY_BYTES:
        raise api_error(
            code="payload_too_large", message="Payload grande", status_code=413
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

    if event_id and _seen_events.seen_before(str(event_id)):
        logger.info("webhook.duplicate event_id=%s", event_id)
        return {"received": True, "handled": False}

    if not item_id or event not in _HANDLED_EVENTS:
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

    background.add_task(_run_sync, connection.id, connection.user_id)
    return {"received": True, "handled": True}
