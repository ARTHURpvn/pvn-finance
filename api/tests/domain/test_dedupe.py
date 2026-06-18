"""RN-05 — deduplicação por provider_transaction_id."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.domain.dedupe import dedupe_by_provider_id
from app.domain.transaction import Transaction


def _tx(provider_id: str) -> Transaction:
    return Transaction.create(
        id=uuid4(),
        user_id=uuid4(),
        account_id=uuid4(),
        provider_transaction_id=provider_id,
        date=date(2026, 1, 1),
        amount=Decimal("-10"),
        description="x",
    )


def test_removes_duplicates_within_batch() -> None:
    txs = [_tx("a"), _tx("b"), _tx("a"), _tx("c"), _tx("b")]
    result = dedupe_by_provider_id(txs)
    assert [t.provider_transaction_id for t in result] == ["a", "b", "c"]


def test_skips_already_persisted_ids() -> None:
    txs = [_tx("a"), _tx("b"), _tx("c")]
    result = dedupe_by_provider_id(txs, existing_provider_ids={"a", "c"})
    assert [t.provider_transaction_id for t in result] == ["b"]


def test_empty_input() -> None:
    assert dedupe_by_provider_id([]) == []
