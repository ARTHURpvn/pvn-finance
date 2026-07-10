"""Rotas de assinaturas — cobranças mensais recorrentes derivadas das
transações (Netflix, Spotify, etc.). Somente leitura."""

from fastapi import APIRouter

from app.api.deps import ApiRateLimit, CurrentUser, SessionDep
from app.api.schemas import SubscriptionResponse, SubscriptionsResponse
from app.domain.subscription import detect, monthly_total
from app.infrastructure.subscription_repository import SqlSubscriptionRepository

router = APIRouter(
    prefix="/subscriptions", tags=["subscriptions"], dependencies=[ApiRateLimit]
)


@router.get("", response_model=SubscriptionsResponse)
def list_subscriptions(
    current_user: CurrentUser, session: SessionDep
) -> SubscriptionsResponse:
    charges = SqlSubscriptionRepository(session).list_candidate_charges(
        current_user.id
    )
    subs = detect(charges)
    return SubscriptionsResponse(
        subscriptions=[
            SubscriptionResponse(
                name=s.name,
                slug=s.slug,
                color=s.color,
                monthly_amount=str(s.monthly_amount),
                occurrences=s.occurrences,
                months=s.months,
                last_date=s.last_date,
                category=s.category,
            )
            for s in subs
        ],
        monthly_total=str(monthly_total(subs)),
    )
