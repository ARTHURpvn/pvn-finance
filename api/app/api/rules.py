"""Rotas do motor de regras de categorização (F7 / FR-015)."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import api_error
from app.api.schemas import RuleCreate, RuleResponse
from app.domain.rule import MatchType, Rule
from app.infrastructure.category_repository import SqlCategoryRepository
from app.infrastructure.rule_repository import SqlRuleRepository

router = APIRouter(prefix="/rules", tags=["rules"])


def _to_response(rule: Rule) -> RuleResponse:
    return RuleResponse(
        id=rule.id,
        match_type=rule.match_type.value,
        pattern=rule.pattern,
        category_id=rule.category_id,
        priority=rule.priority,
    )


@router.get("", response_model=list[RuleResponse])
def list_rules(current_user: CurrentUser, session: SessionDep) -> list[RuleResponse]:
    return [_to_response(r) for r in SqlRuleRepository(session).list_for_user(current_user.id)]


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate, current_user: CurrentUser, session: SessionDep
) -> RuleResponse:
    # Garante que a categoria pertence ao usuário (ou é de sistema).
    if SqlCategoryRepository(session).get_for_user(body.category_id, current_user.id) is None:
        raise api_error(
            code="category_not_found",
            message="Categoria inválida",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    rule = SqlRuleRepository(session).add(
        user_id=current_user.id,
        match_type=MatchType(body.match_type),
        pattern=body.pattern,
        category_id=body.category_id,
        priority=body.priority,
    )
    return _to_response(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: UUID, current_user: CurrentUser, session: SessionDep
) -> None:
    if not SqlRuleRepository(session).delete(rule_id, current_user.id):
        raise api_error(
            code="rule_not_found",
            message="Regra não encontrada",
            status_code=status.HTTP_404_NOT_FOUND,
        )
