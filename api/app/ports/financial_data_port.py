"""FinancialDataPort — contrato do agregador (ADR-002).

O domínio não conhece Pluggy: depende apenas desta interface. Os DTOs
abaixo espelham o modelo canônico do Open Finance (forma "provider"),
que a normalização traduz para as entidades de domínio. Trocar de
agregador = novo adapter implementando esta Port."""

from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol


class AggregatorError(Exception):
    """Falha não-recuperável ao falar com o agregador."""


class RetryableAggregatorError(AggregatorError):
    """Falha transitória (429/529/5xx/rede) — elegível a retry com backoff."""


@dataclass(frozen=True, slots=True)
class ProviderAccount:
    """Conta na forma do agregador (pré-normalização)."""

    provider_account_id: str
    type: str
    name: str
    currency: str
    balance: Decimal
    balance_updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ProviderTransaction:
    """Transação na forma do agregador (pré-normalização)."""

    provider_transaction_id: str
    date: date_type
    amount: Decimal
    description: str
    counterpart: str | None = None
    provider_category: str | None = None
    raw: dict[str, Any] | None = None


class FinancialDataPort(Protocol):
    """Contrato do agregador: emissão de connect token + leitura de dados."""

    def create_connect_token(self, *, item_id: str | None = None) -> str:
        """Emite o token do widget de conexão (com item_id = reauth)."""
        ...

    def fetch_accounts(self, *, provider_item_id: str) -> list[ProviderAccount]:
        """Lista as contas de uma conexão."""
        ...

    def fetch_transactions(
        self,
        *,
        provider_item_id: str,
        provider_account_id: str,
        since: date_type | None = None,
    ) -> list[ProviderTransaction]:
        """Lista transações de uma conta, opcionalmente desde ``since``."""
        ...
