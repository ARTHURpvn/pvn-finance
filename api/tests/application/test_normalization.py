"""Normalização provider → domínio."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.normalization import normalize_account, normalize_transaction
from app.domain.account import AccountType
from app.domain.transaction import Direction
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


def test_normalize_account_maps_fields() -> None:
    provider = ProviderAccount(
        provider_account_id="acc-1",
        type="credit_card",
        name="Cartão",
        currency="BRL",
        balance=Decimal("-200.00"),
    )

    account = normalize_account(
        provider, user_id=uuid4(), connection_id=uuid4(), account_id=uuid4()
    )

    assert account.type == AccountType.CREDIT_CARD
    assert account.provider_account_id == "acc-1"
    assert account.balance == Decimal("-200.00")


def test_normalize_account_rejects_unknown_type() -> None:
    provider = ProviderAccount(
        provider_account_id="acc-1",
        type="cripto",
        name="x",
        currency="BRL",
        balance=Decimal("0"),
    )
    with pytest.raises(ValueError):
        normalize_account(
            provider, user_id=uuid4(), connection_id=uuid4(), account_id=uuid4()
        )


def test_normalize_transaction_derives_direction() -> None:
    provider = ProviderTransaction(
        provider_transaction_id="ptx-1",
        date=date(2026, 1, 1),
        amount=Decimal("-99.90"),
        description="Compra",
    )

    tx = normalize_transaction(
        provider, user_id=uuid4(), account_id=uuid4(), transaction_id=uuid4()
    )

    assert tx.direction == Direction.OUT
    assert tx.provider_transaction_id == "ptx-1"
    assert tx.amount == Decimal("-99.90")


def test_credit_card_purchase_inverts_sign_to_expense() -> None:
    # No cartão o Pluggy manda a compra positiva (aumenta a fatura); é gasto.
    provider = ProviderTransaction(
        provider_transaction_id="c1",
        date=date(2026, 1, 5),
        amount=Decimal("54.96"),
        description="SUP MEDEIROS",
    )

    tx = normalize_transaction(
        provider,
        user_id=uuid4(),
        account_id=uuid4(),
        transaction_id=uuid4(),
        is_credit_card=True,
    )

    assert tx.amount == Decimal("-54.96")
    assert tx.direction == Direction.OUT  # vira gasto


def test_credit_card_bill_reduction_is_neutral() -> None:
    # Redução da fatura (pagamento/estorno vem negativo no cartão) não é receita.
    provider = ProviderTransaction(
        provider_transaction_id="p1",
        date=date(2026, 1, 6),
        amount=Decimal("-500.00"),
        description="Pagamento recebido",
    )

    tx = normalize_transaction(
        provider,
        user_id=uuid4(),
        account_id=uuid4(),
        transaction_id=uuid4(),
        is_credit_card=True,
    )

    assert tx.amount == Decimal("500.00")
    assert tx.is_transfer is True  # neutro: não infla o Entrou
