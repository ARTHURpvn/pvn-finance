"""Adapter SQLAlchemy do repositório de regras."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.rule import MatchType, Rule
from app.infrastructure.models import RuleModel


class SqlRuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: RuleModel) -> Rule:
        return Rule(
            id=model.id,
            user_id=model.user_id,
            match_type=MatchType(model.match_type),
            pattern=model.pattern,
            category_id=model.category_id,
            priority=model.priority,
        )

    def list_for_user(self, user_id: UUID) -> list[Rule]:
        stmt = (
            select(RuleModel)
            .where(RuleModel.user_id == user_id)
            .order_by(RuleModel.priority)
        )
        return [self._to_domain(m) for m in self._session.scalars(stmt)]

    def add(
        self,
        *,
        user_id: UUID,
        match_type: MatchType,
        pattern: str,
        category_id: UUID,
        priority: int = 100,
    ) -> Rule:
        model = RuleModel(
            user_id=user_id,
            match_type=match_type.value,
            pattern=pattern,
            category_id=category_id,
            priority=priority,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def delete(self, rule_id: UUID, user_id: UUID) -> bool:
        model = self._session.get(RuleModel, rule_id)
        if model is None or model.user_id != user_id:
            return False
        self._session.delete(model)
        self._session.commit()
        return True
