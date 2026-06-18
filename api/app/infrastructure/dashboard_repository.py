"""Agregações do dashboard (F8). Queries SQL agrupadas, apoiadas no índice
transactions(user_id, date) — NFR-005."""

from dataclasses import dataclass
from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.transaction import Direction
from app.infrastructure.models import CategoryModel, TransactionModel

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class Summary:
    received: Decimal
    spent: Decimal
    net: Decimal


@dataclass(frozen=True, slots=True)
class CategorySpend:
    category: str
    total: Decimal


@dataclass(frozen=True, slots=True)
class TimelinePoint:
    month: str
    inflow: Decimal
    outflow: Decimal


class SqlDashboardRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _date_filter(
        self, conditions: list, date_from: date_type | None, date_to: date_type | None
    ) -> list:
        if date_from is not None:
            conditions.append(TransactionModel.date >= date_from)
        if date_to is not None:
            conditions.append(TransactionModel.date <= date_to)
        return conditions

    def summary(
        self, user_id: UUID, date_from: date_type | None, date_to: date_type | None
    ) -> Summary:
        conditions = self._date_filter(
            [TransactionModel.user_id == user_id], date_from, date_to
        )
        stmt = (
            select(
                TransactionModel.direction,
                func.coalesce(func.sum(TransactionModel.amount), _ZERO),
            )
            .where(*conditions)
            .group_by(TransactionModel.direction)
        )
        received = _ZERO
        spent = _ZERO
        for direction, total in self._session.execute(stmt):
            if direction == Direction.IN.value:
                received = total
            else:
                spent = -total  # 'out' soma negativo → gasto positivo
        return Summary(received=received, spent=spent, net=received - spent)

    def by_category(
        self, user_id: UUID, date_from: date_type | None, date_to: date_type | None
    ) -> list[CategorySpend]:
        conditions = self._date_filter(
            [
                TransactionModel.user_id == user_id,
                TransactionModel.direction == Direction.OUT.value,
            ],
            date_from,
            date_to,
        )
        stmt = (
            select(
                CategoryModel.name,
                func.coalesce(func.sum(TransactionModel.amount), _ZERO),
            )
            .select_from(TransactionModel)
            .outerjoin(CategoryModel, TransactionModel.category_id == CategoryModel.id)
            .where(*conditions)
            .group_by(CategoryModel.name)
        )
        result = [
            CategorySpend(category=name or "Sem categoria", total=-total)
            for name, total in self._session.execute(stmt)
        ]
        result.sort(key=lambda c: c.total, reverse=True)
        return result

    def timeline(
        self, user_id: UUID, date_from: date_type | None, date_to: date_type | None
    ) -> list[TimelinePoint]:
        month = func.to_char(func.date_trunc("month", TransactionModel.date), "YYYY-MM")
        conditions = self._date_filter(
            [TransactionModel.user_id == user_id], date_from, date_to
        )
        stmt = (
            select(
                month.label("month"),
                TransactionModel.direction,
                func.coalesce(func.sum(TransactionModel.amount), _ZERO),
            )
            .where(*conditions)
            .group_by("month", TransactionModel.direction)
            .order_by("month")
        )
        points: dict[str, dict[str, Decimal]] = {}
        for m, direction, total in self._session.execute(stmt):
            bucket = points.setdefault(m, {"in": _ZERO, "out": _ZERO})
            if direction == Direction.IN.value:
                bucket["in"] = total
            else:
                bucket["out"] = -total
        return [
            TimelinePoint(month=m, inflow=v["in"], outflow=v["out"])
            for m, v in sorted(points.items())
        ]
