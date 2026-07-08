"""Conexão (Item no Pluggy) — vínculo de um banco via agregador."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConnectionStatus(StrEnum):
    ATIVA = "ativa"
    REQUER_REAUTH = "requer_reauth"
    ERRO = "erro"


#: Status do Item (Pluggy) que exigem ação do usuário → RN-03 (requer_reauth).
_ITEM_STATUS_REAUTH = frozenset(
    {"LOGIN_ERROR", "WAITING_USER_INPUT", "WAITING_USER_ACTION"}
)
#: Status do Item que indicam sucesso (dados prontos) → conexão ativa.
_ITEM_STATUS_OK = frozenset({"UPDATED"})
#: Status do Item de falha sistêmica/transitória → erro.
_ITEM_STATUS_ERROR = frozenset({"OUTDATED", "ERROR"})


def connection_status_from_item(
    item_status: str,
    *,
    consent_expires_at: datetime | None,
    now: datetime,
) -> "ConnectionStatus | None":
    """Mapeia o status do Item do agregador para o status da conexão (RN-03).

    Retorna ``None`` para estados em progresso ou desconhecidos (não terminais):
    o chamador deve preservar o status atual. Consentimento expirado tem
    precedência sobre o status reportado."""
    if consent_expires_at is not None and now >= consent_expires_at:
        return ConnectionStatus.REQUER_REAUTH
    status = item_status.upper()
    if status in _ITEM_STATUS_REAUTH:
        return ConnectionStatus.REQUER_REAUTH
    if status in _ITEM_STATUS_OK:
        return ConnectionStatus.ATIVA
    if status in _ITEM_STATUS_ERROR:
        return ConnectionStatus.ERRO
    return None


@dataclass(frozen=True, slots=True)
class Connection:
    """Conexão de uma instituição. O segredo do agregador NÃO vive no
    domínio (fica cifrado na infraestrutura — ADR-005)."""

    id: UUID
    user_id: UUID
    provider: str
    provider_item_id: str
    institution_name: str
    status: ConnectionStatus
    consent_expires_at: datetime | None = None
    last_sync_at: datetime | None = None

    def is_consent_expired(self, now: datetime) -> bool:
        """True se o consentimento já expirou (base para RN-03 na F5)."""
        return self.consent_expires_at is not None and now >= self.consent_expires_at
