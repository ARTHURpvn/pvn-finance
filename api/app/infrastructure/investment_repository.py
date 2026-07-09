"""Adapter SQLAlchemy do repositório de investimentos."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.investment import Investment
from app.infrastructure.models import InvestmentModel
from app.ports.financial_data_port import ProviderInvestment


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
        )

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
                subtype=provider_investment.subtype,
                balance=provider_investment.balance,
                currency=provider_investment.currency,
            )
            self._session.add(model)
        else:
            model.name = provider_investment.name
            model.type = provider_investment.type
            model.subtype = provider_investment.subtype
            model.balance = provider_investment.balance
            model.currency = provider_investment.currency
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def list_by_user(self, user_id: UUID) -> list[Investment]:
        stmt = select(InvestmentModel).where(InvestmentModel.user_id == user_id)
        return [self._to_domain(m) for m in self._session.scalars(stmt)]
