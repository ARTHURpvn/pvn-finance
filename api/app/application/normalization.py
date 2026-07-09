"""Normalização: DTOs do agregador → entidades de domínio.

Depende de domain (regras) e ports (DTOs) — nunca de um adapter concreto.
Aplica RN-01 (sinal) ao traduzir transações."""

from uuid import UUID

from app.domain.account import Account, AccountType
from app.domain.transaction import Transaction, is_flow_neutral
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


def normalize_account(
    provider: ProviderAccount,
    *,
    user_id: UUID,
    connection_id: UUID,
    account_id: UUID,
) -> Account:
    """Traduz uma conta do agregador para o domínio. ``type`` desconhecido
    levanta ValueError (validação na fronteira)."""
    return Account(
        id=account_id,
        user_id=user_id,
        connection_id=connection_id,
        provider_account_id=provider.provider_account_id,
        type=AccountType(provider.type),
        name=provider.name,
        currency=provider.currency,
        balance=provider.balance,
        balance_updated_at=provider.balance_updated_at,
    )


def normalize_transaction(
    provider: ProviderTransaction,
    *,
    user_id: UUID,
    account_id: UUID,
    transaction_id: UUID,
    category_id: UUID | None = None,
) -> Transaction:
    """Traduz uma transação do agregador para o domínio, derivando o sinal
    (RN-01) via ``Transaction.create``."""
    return Transaction.create(
        id=transaction_id,
        user_id=user_id,
        account_id=account_id,
        provider_transaction_id=provider.provider_transaction_id,
        date=provider.date,
        amount=provider.amount,
        description=provider.description,
        counterpart=provider.counterpart,
        category_id=category_id,
        is_transfer=is_flow_neutral(provider.provider_category),
    )
