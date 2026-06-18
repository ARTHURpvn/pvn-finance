"""Schemas Pydantic da API de autenticação (entrada/saída).

Nenhum schema de saída inclui senha ou hash (NFR-001)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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


class AccessTokenResponse(BaseModel):
    access_token: str
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
