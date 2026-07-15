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
    """Falha transitória (429/529/5xx/rede) — elegível a retry com backoff.

    ``retry_after`` (segundos) carrega o header ``Retry-After`` de um 429,
    honrado como atraso mínimo pelo backoff (NFR-004)."""

    def __init__(self, message: str = "", *, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


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


@dataclass(frozen=True, slots=True)
class ProviderItem:
    """Item (conexão) na forma do agregador — status e consentimento.

    Espelha ``GET /items/{id}`` do Pluggy: ``status``/``execution_status``
    dirigem RN-03 (requer_reauth); ``consent_expires_at`` alimenta o check
    de expiração do consentimento."""

    provider_item_id: str
    status: str
    execution_status: str | None = None
    consent_expires_at: datetime | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderInvestment:
    """Investimento na forma do agregador (pré-normalização).

    ``balance`` é o valor atual (net worth) da posição — usado para compor o
    patrimônio total (ex.: BB Rende Fácil, CDBs, fundos)."""

    provider_investment_id: str
    name: str
    type: str
    balance: Decimal
    currency: str = "BRL"
    subtype: str | None = None
    # Detalhe (renda fixa mensal, ganho/perda, evolução, banco).
    amount_original: Decimal | None = None
    amount_profit: Decimal | None = None
    value: Decimal | None = None
    quantity: Decimal | None = None
    rate: Decimal | None = None
    rate_type: str | None = None
    annual_rate: Decimal | None = None
    last_month_rate: Decimal | None = None
    last_twelve_months_rate: Decimal | None = None
    due_date: date_type | None = None
    purchase_date: date_type | None = None
    institution: str | None = None


class FinancialDataPort(Protocol):
    """Contrato do agregador: emissão de connect token + leitura de dados."""

    def create_connect_token(
        self,
        *,
        item_id: str | None = None,
        webhook_url: str | None = None,
        client_user_id: str | None = None,
    ) -> str:
        """Emite o token do widget de conexão.

        ``item_id`` habilita reauth (FR-005); ``webhook_url`` inscreve o item
        para notificações (senão o item nunca notifica); ``client_user_id``
        vincula o item ao usuário do nosso lado."""
        ...

    def fetch_item(self, *, provider_item_id: str) -> ProviderItem:
        """Lê o estado atual do item no agregador (status + consentimento)."""
        ...

    def fetch_accounts(self, *, provider_item_id: str) -> list[ProviderAccount]:
        """Lista as contas de uma conexão."""
        ...

    def fetch_investments(
        self, *, provider_item_id: str
    ) -> list[ProviderInvestment]:
        """Lista os investimentos de uma conexão (compõem o patrimônio)."""
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
