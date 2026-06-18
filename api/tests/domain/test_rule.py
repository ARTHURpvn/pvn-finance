"""Entidade Rule (o motor de aplicação chega na F7)."""

from uuid import uuid4

from app.domain.rule import MatchType, Rule


def test_rule_construction() -> None:
    category_id = uuid4()
    rule = Rule(
        id=uuid4(),
        user_id=uuid4(),
        match_type=MatchType.CONTAINS,
        pattern="iFood",
        category_id=category_id,
        priority=10,
    )

    assert rule.match_type == MatchType.CONTAINS
    assert rule.pattern == "iFood"
    assert rule.category_id == category_id
    assert rule.priority == 10


def test_match_type_values() -> None:
    assert {m.value for m in MatchType} == {"contains", "equals", "regex"}
