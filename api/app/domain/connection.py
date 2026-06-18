"""Conexão (Item no Pluggy) — vínculo de um banco via agregador."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConnectionStatus(StrEnum):
    ATIVA = "ativa"
    REQUER_REAUTH = "requer_reauth"
    ERRO = "erro"


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
