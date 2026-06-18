"""Motor de categorização (ADR-004) e Rule.matches."""

from uuid import uuid4

from app.domain.categorization import categorize
from app.domain.category import Category, CategoryKind
from app.domain.rule import MatchType, Rule


def _rule(pattern: str, category_id, *, match=MatchType.CONTAINS, priority=100) -> Rule:
    return Rule(
        id=uuid4(),
        user_id=uuid4(),
        match_type=match,
        pattern=pattern,
        category_id=category_id,
        priority=priority,
    )


def _cat(name: str, cid) -> Category:
    return Category(id=cid, name=name, kind=CategoryKind.EXPENSE, is_system=True)


def test_matches_contains_case_insensitive() -> None:
    rule = _rule("iFood", uuid4())
    assert rule.matches("COMPRA IFOOD *123") is True
    assert rule.matches("mercado") is False


def test_matches_equals_and_regex() -> None:
    eq = _rule("netflix.com", uuid4(), match=MatchType.EQUALS)
    assert eq.matches("NETFLIX.COM") is True
    assert eq.matches("netflix.com br") is False

    rx = _rule(r"uber\s*eats", uuid4(), match=MatchType.REGEX)
    assert rx.matches("UBER EATS 123") is True


def test_invalid_regex_is_safe() -> None:
    bad = _rule("[unclosed", uuid4(), match=MatchType.REGEX)
    assert bad.matches("qualquer") is False


def test_precedence_rule_wins_over_provider_and_fallback() -> None:
    target = uuid4()
    fallback = uuid4()
    cat_id = uuid4()
    result = categorize(
        description="Pedido iFood",
        provider_category="Restaurants",
        rules=[_rule("ifood", target)],
        categories=[_cat("Restaurants", cat_id)],
        fallback_id=fallback,
    )
    assert result == target


def test_precedence_provider_when_no_rule() -> None:
    cat_id = uuid4()
    result = categorize(
        description="algo",
        provider_category="Alimentação",
        rules=[],
        categories=[_cat("Alimentação", cat_id)],
        fallback_id=uuid4(),
    )
    assert result == cat_id


def test_precedence_fallback_when_nothing_matches() -> None:
    fallback = uuid4()
    result = categorize(
        description="xyz",
        provider_category="Desconhecida",
        rules=[],
        categories=[_cat("Alimentação", uuid4())],
        fallback_id=fallback,
    )
    assert result == fallback


def test_lower_priority_number_wins() -> None:
    first = uuid4()
    second = uuid4()
    result = categorize(
        description="mercado livre",
        provider_category=None,
        rules=[
            _rule("mercado", second, priority=100),
            _rule("mercado", first, priority=1),
        ],
        categories=[],
        fallback_id=None,
    )
    assert result == first
