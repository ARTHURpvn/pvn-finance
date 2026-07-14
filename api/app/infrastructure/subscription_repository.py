"""Fetch das cobranças candidatas a assinatura (F: assinaturas).

Prefiltra no SQL (categoria de streaming OU descrição casando com o catálogo)
para não trazer todas as transações; a decisão final é do domínio."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.subscription import CATALOG, STREAMING_CATEGORIES, Charge
from app.domain.transaction import Direction
from app.infrastructure.models import TransactionModel

#: Regex único combinando os padrões do catálogo, aplicado no Postgres (~*).
_BRAND_REGEX = "|".join(f"({b.pattern.pattern})" for b in CATALOG)


class SqlSubscriptionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_candidate_charges(self, user_id: UUID) -> list[Charge]:
        category = TransactionModel.raw["category"].astext
        stmt = select(
            TransactionModel.date,
            TransactionModel.amount,
            TransactionModel.description,
            category,
        ).where(
            TransactionModel.user_id == user_id,
            TransactionModel.direction == Direction.OUT.value,
            TransactionModel.is_transfer.is_(False),
            or_(
                func.lower(category).in_(sorted(STREAMING_CATEGORIES)),
                TransactionModel.description.op("~*")(_BRAND_REGEX),
            ),
        )
        return [
            Charge(
                date=date,
                amount=amount,
                description=description or "",
                provider_category=cat,
            )
            for date, amount, description, cat in self._session.execute(stmt)
        ]
