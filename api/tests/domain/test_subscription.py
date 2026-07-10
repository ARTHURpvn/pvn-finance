"""Detecção de assinaturas recorrentes a partir de cobranças."""

from datetime import date
from decimal import Decimal

from app.domain.subscription import (
    Charge,
    detect,
    match_brand,
    monthly_total,
)


def _charge(y: int, m: int, amount: str, desc: str, cat: str | None = None) -> Charge:
    return Charge(
        date=date(y, m, 1),
        amount=Decimal(amount),
        description=desc,
        provider_category=cat,
    )


def test_match_brand_by_description() -> None:
    b = match_brand("COMPRA C/CARTAO 08/07 NETFLIX.COM", "Video streaming")
    assert b is not None and b.name == "Netflix" and b.slug == "netflix"
    assert match_brand("PIX MERCADO LIVRE", None) is None


def test_detects_recurring_subscription_uses_latest_amount() -> None:
    charges = [
        _charge(2026, 5, "-55.90", "NETFLIX.COM", "Video streaming"),
        _charge(2026, 6, "-59.90", "NETFLIX.COM", "Video streaming"),
        _charge(2026, 7, "-59.90", "NETFLIX.COM", "Video streaming"),
    ]
    subs = detect(charges)
    assert len(subs) == 1
    s = subs[0]
    assert s.name == "Netflix"
    assert s.monthly_amount == Decimal("59.90")  # cobrança mais recente
    assert s.occurrences == 3
    assert s.months == 3
    assert s.last_date == date(2026, 7, 1)


def test_single_month_charge_is_not_a_subscription() -> None:
    charges = [_charge(2026, 7, "-9.90", "APPLE.COM/BILL", "Music streaming")]
    assert detect(charges) == []


def test_multiple_services_sorted_by_amount_desc() -> None:
    charges = [
        _charge(2026, 6, "-12.90", "SPOTIFY", "Music streaming"),
        _charge(2026, 7, "-12.90", "SPOTIFY", "Music streaming"),
        _charge(2026, 6, "-59.90", "NETFLIX.COM", "Video streaming"),
        _charge(2026, 7, "-59.90", "NETFLIX.COM", "Video streaming"),
    ]
    subs = detect(charges)
    assert [s.name for s in subs] == ["Netflix", "Spotify"]
    assert monthly_total(subs) == Decimal("72.80")


def test_streaming_category_without_known_brand_groups_generic() -> None:
    charges = [
        _charge(2026, 6, "-19.90", "SERVICO XPTO STREAM", "Video streaming"),
        _charge(2026, 7, "-19.90", "SERVICO XPTO STREAM", "Video streaming"),
    ]
    subs = detect(charges)
    assert len(subs) == 1
    assert subs[0].slug == ""  # sem logo → avatar genérico no frontend
    assert subs[0].monthly_amount == Decimal("19.90")
