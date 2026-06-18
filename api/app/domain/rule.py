"""Regra de categorização do usuário (entidade) + match (F7)."""

import re
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

    def matches(self, description: str) -> bool:
        """True se a descrição casa com o padrão (case-insensitive)."""
        desc = description.lower()
        pattern = self.pattern.lower()
        if self.match_type == MatchType.CONTAINS:
            return pattern in desc
        if self.match_type == MatchType.EQUALS:
            return desc == pattern
        if self.match_type == MatchType.REGEX:
            try:
                return re.search(self.pattern, description, re.IGNORECASE) is not None
            except re.error:
                return False
        return False
