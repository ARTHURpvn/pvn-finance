"""Adapter fake do FinancialDataPort."""

from datetime import date
from decimal import Decimal

from app.adapters.fake import FakeFinancialDataAdapter
from app.ports.financial_data_port import ProviderAccount, ProviderTransaction


def test_fake_returns_configured_data() -> None:
    account = ProviderAccount(
        provider_account_id="acc-1",
        type="checking",
        name="Conta",
        currency="BRL",
        balance=Decimal("100"),
    )
    tx = ProviderTransaction(
        provider_transaction_id="tx-1",
        date=date(2026, 1, 1),
        amount=Decimal("-10"),
        description="x",
    )
    adapter = FakeFinancialDataAdapter(
        accounts=[account], transactions={"acc-1": [tx]}
    )

    assert adapter.fetch_accounts(provider_item_id="item-1") == [account]
    assert adapter.fetch_transactions(
        provider_item_id="item-1", provider_account_id="acc-1"
    ) == [tx]
    assert adapter.fetch_transactions(
        provider_item_id="item-1", provider_account_id="missing"
    ) == []
    assert adapter.create_connect_token() == "fake-connect-token"
