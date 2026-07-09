"""Schemas Pydantic da API de autenticação (entrada/saída).

Nenhum schema de saída inclui senha ou hash (NFR-001)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime


# ---- Conexões (F5) -------------------------------------------------------


class ConnectTokenResponse(BaseModel):
    connect_token: str


class RegisterConnectionRequest(BaseModel):
    provider_item_id: str = Field(min_length=1, max_length=255)
    institution_name: str = Field(min_length=1, max_length=255)


class ConnectionResponse(BaseModel):
    id: UUID
    provider: str
    institution_name: str
    status: str
    consent_expires_at: datetime | None = None
    last_sync_at: datetime | None = None


class SyncResultResponse(BaseModel):
    status: str
    imported: int


# ---- Contas & transações (F6) -------------------------------------------


class AccountResponse(BaseModel):
    id: UUID
    connection_id: UUID
    type: str
    name: str
    currency: str
    balance: str  # decimal como string (convenção da API)
    balance_updated_at: datetime | None = None


class AccountSummary(BaseModel):
    total: str  # saldo disponível: contas de depósito + reservas de liquidez
    cash: str  # só saldo em conta corrente
    reserves: str  # reservas de liquidez (Rende Fácil) — contam no saldo
    investments: str  # investimentos de prazo (CDB, fundos) — à parte
    credit_card: str


class InvestmentResponse(BaseModel):
    name: str
    type: str
    balance: str
    is_reserve: bool  # reserva de liquidez (conta como saldo do banco)


class AccountsResponse(BaseModel):
    accounts: list[AccountResponse]
    investments: list[InvestmentResponse]
    summary: AccountSummary


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    account_type: str | None = None  # ex.: credit_card (para destaque no extrato)
    account_name: str | None = None  # nome da conta (para exibir a logo do banco)
    date: date
    amount: str
    direction: str
    description: str
    counterpart: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None


class TransactionsPage(BaseModel):
    items: list[TransactionResponse]
    page: int
    page_size: int
    total: int


# ---- Categorização (F7) --------------------------------------------------


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    kind: str
    is_system: bool
    parent_id: UUID | None = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: str = Field(pattern="^(income|expense|transfer)$")
    parent_id: UUID | None = None


class RuleResponse(BaseModel):
    id: UUID
    match_type: str
    pattern: str
    category_id: UUID
    priority: int


class RuleCreate(BaseModel):
    match_type: str = Field(pattern="^(contains|equals|regex)$")
    pattern: str = Field(min_length=1, max_length=255)
    category_id: UUID
    priority: int = 100


class RecategorizeRequest(BaseModel):
    category_id: UUID
    create_rule: bool = False


# ---- Dashboard (F8) ------------------------------------------------------


class DashboardSummary(BaseModel):
    received: str
    spent: str
    net: str


class CategorySpendResponse(BaseModel):
    category: str
    total: str


class TimelinePointResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    month: str
    inflow: str = Field(serialization_alias="in")
    outflow: str = Field(serialization_alias="out")
