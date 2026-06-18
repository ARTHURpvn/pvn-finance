"""RN-01 (sinal) e RN-04 (imutabilidade) da Transaction."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.transaction import Direction, Transaction


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("100.50"), Direction.IN),
        (Decimal("0"), Direction.IN),
        (Decimal("-1"), Direction.OUT),
        (Decimal("-999.99"), Direction.OUT),
    ],
)
def test_direction_from_amount(amount: Decimal, expected: Direction) -> None:
    assert Direction.from_amount(amount) == expected


def _make_tx(amount: Decimal, category_id=None) -> Transaction:
    return Transaction.create(
        id=uuid4(),
        user_id=uuid4(),
        account_id=uuid4(),
        provider_transaction_id="ptx-1",
        date=date(2026, 1, 1),
        amount=amount,
        description="Mercado XPTO",
        category_id=category_id,
    )


def test_create_derives_direction() -> None:
    assert _make_tx(Decimal("-50")).direction == Direction.OUT
    assert _make_tx(Decimal("50")).direction == Direction.IN


def test_recategorize_returns_new_instance_changing_only_category() -> None:
    original = _make_tx(Decimal("-50"))
    new_category = uuid4()

    updated = original.recategorize(new_category)

    assert updated is not original
    assert updated.category_id == new_category
    assert original.category_id is None  # original intacto (RN-04)
    # todos os demais campos preservados
    assert updated.id == original.id
    assert updated.amount == original.amount
    assert updated.direction == original.direction
    assert updated.provider_transaction_id == original.provider_transaction_id


def test_transaction_is_frozen() -> None:
    tx = _make_tx(Decimal("10"))
    with pytest.raises(AttributeError):
        tx.amount = Decimal("20")  # type: ignore[misc]
