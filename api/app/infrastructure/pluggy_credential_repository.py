"""Repositório das credenciais Pluggy por usuário (multi-tenant).

O client_secret é cifrado em repouso (CredentialVault/Fernet) e só é decifrado
para construir o adapter — nunca sai pela API."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import PluggyCredentialModel
from app.infrastructure.vault import CredentialVault


@dataclass(frozen=True, slots=True)
class PluggyCredentials:
    client_id: str
    client_secret: str
    base_url: str


@dataclass(frozen=True, slots=True)
class PluggyCredentialStatus:
    configured: bool
    client_id: str | None
    base_url: str | None


class SqlPluggyCredentialRepository:
    def __init__(self, session: Session, vault: CredentialVault) -> None:
        self._session = session
        self._vault = vault

    def _get_model(self, user_id: UUID) -> PluggyCredentialModel | None:
        return self._session.scalar(
            select(PluggyCredentialModel).where(
                PluggyCredentialModel.user_id == user_id
            )
        )

    def get(self, user_id: UUID) -> PluggyCredentials | None:
        """Credenciais completas (com o segredo decifrado) — uso interno para
        construir o adapter. None se o usuário não configurou."""
        m = self._get_model(user_id)
        if m is None:
            return None
        return PluggyCredentials(
            client_id=m.client_id,
            client_secret=self._vault.decrypt(m.encrypted_client_secret),
            base_url=m.base_url,
        )

    def status(self, user_id: UUID) -> PluggyCredentialStatus:
        """Status para a API — NUNCA inclui o segredo."""
        m = self._get_model(user_id)
        if m is None:
            return PluggyCredentialStatus(configured=False, client_id=None, base_url=None)
        return PluggyCredentialStatus(
            configured=True, client_id=m.client_id, base_url=m.base_url
        )

    def upsert(
        self, *, user_id: UUID, client_id: str, client_secret: str, base_url: str
    ) -> None:
        encrypted = self._vault.encrypt(client_secret)
        m = self._get_model(user_id)
        if m is None:
            m = PluggyCredentialModel(
                user_id=user_id,
                client_id=client_id,
                encrypted_client_secret=encrypted,
                base_url=base_url,
            )
            self._session.add(m)
        else:
            m.client_id = client_id
            m.encrypted_client_secret = encrypted
            m.base_url = base_url
        self._session.commit()

    def delete(self, user_id: UUID) -> bool:
        m = self._get_model(user_id)
        if m is None:
            return False
        self._session.delete(m)
        self._session.commit()
        return True
