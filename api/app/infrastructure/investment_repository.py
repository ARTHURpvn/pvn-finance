"""Adapter SQLAlchemy do repositório de investimentos."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.investment import Investment
from app.infrastructure.models import InvestmentModel
from app.ports.financial_data_port import ProviderInvestment

# Campos de detalhe copiados 1:1 de ProviderInvestment → InvestmentModel.
_DETAIL_FIELDS = (
    "amount_original",
    "amount_profit",
    "value",
    "quantity",
    "rate",
    "rate_type",
    "annual_rate",
    "last_month_rate",
    "last_twelve_months_rate",
    "due_date",
    "purchase_date",
    "institution",
)


class SqlInvestmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: InvestmentModel) -> Investment:
        return Investment(
            id=model.id,
            user_id=model.user_id,
            connection_id=model.connection_id,
            provider_investment_id=model.provider_investment_id,
            name=model.name,
            type=model.type,
            subtype=model.subtype,
            balance=model.balance,
            currency=model.currency,
            **{f: getattr(model, f) for f in _DETAIL_FIELDS},
        )

    @staticmethod
    def _apply(model: InvestmentModel, provider: ProviderInvestment) -> None:
        model.name = provider.name
        model.type = provider.type
        model.subtype = provider.subtype
        model.balance = provider.balance
        model.currency = provider.currency
        for f in _DETAIL_FIELDS:
            setattr(model, f, getattr(provider, f))

    def upsert(
        self,
        *,
        user_id: UUID,
        connection_id: UUID,
        provider_investment: ProviderInvestment,
    ) -> Investment:
        """Cria/atualiza por (connection_id, provider_investment_id)."""
        stmt = select(InvestmentModel).where(
            InvestmentModel.connection_id == connection_id,
            InvestmentModel.provider_investment_id
            == provider_investment.provider_investment_id,
        )
        model = self._session.scalar(stmt)
        if model is None:
            model = InvestmentModel(
                user_id=user_id,
                connection_id=connection_id,
                provider_investment_id=provider_investment.provider_investment_id,
                name=provider_investment.name,
                type=provider_investment.type,
                balance=provider_investment.balance,
                currency=provider_investment.currency,
            )
            self._apply(model, provider_investment)
            self._session.add(model)
        else:
            self._apply(model, provider_investment)
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def list_by_user(self, user_id: UUID) -> list[Investment]:
        stmt = select(InvestmentModel).where(InvestmentModel.user_id == user_id)
        return [self._to_domain(m) for m in self._session.scalars(stmt)]
