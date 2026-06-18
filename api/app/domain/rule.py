"""Regra de categorização do usuário (entidade). O motor de aplicação das
regras (precedência, match) chega na F7."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class MatchType(StrEnum):
    CONTAINS = "contains"
    EQUALS = "equals"
    REGEX = "regex"


@dataclass(frozen=True, slots=True)
class Rule:
    id: UUID
    user_id: UUID
    match_type: MatchType
    pattern: str
    category_id: UUID
    priority: int
