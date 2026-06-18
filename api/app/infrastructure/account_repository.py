"""Adapter SQLAlchemy do repositório de contas."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.account import Account, AccountType
from app.infrastructure.models import AccountModel
from app.ports.financial_data_port import ProviderAccount


class SqlAccountRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            user_id=model.user_id,
            connection_id=model.connection_id,
            provider_account_id=model.provider_account_id,
            type=AccountType(model.type),
            name=model.name,
            currency=model.currency,
            balance=model.balance,
            balance_updated_at=model.balance_updated_at,
        )

    def upsert(
        self, *, user_id: UUID, connection_id: UUID, provider_account: ProviderAccount
    ) -> Account:
        """Cria ou atualiza a conta por (connection_id, provider_account_id)."""
        stmt = select(AccountModel).where(
            AccountModel.connection_id == connection_id,
            AccountModel.provider_account_id == provider_account.provider_account_id,
        )
        model = self._session.scalar(stmt)
        if model is None:
            model = AccountModel(
                user_id=user_id,
                connection_id=connection_id,
                provider_account_id=provider_account.provider_account_id,
                type=provider_account.type,
                name=provider_account.name,
                currency=provider_account.currency,
                balance=provider_account.balance,
                balance_updated_at=provider_account.balance_updated_at,
            )
            self._session.add(model)
        else:
            model.type = provider_account.type
            model.name = provider_account.name
            model.currency = provider_account.currency
            model.balance = provider_account.balance
            model.balance_updated_at = provider_account.balance_updated_at
        self._session.commit()
        self._session.refresh(model)
        return self._to_domain(model)

    def list_by_user(self, user_id: UUID) -> list[Account]:
        stmt = select(AccountModel).where(AccountModel.user_id == user_id)
        return [self._to_domain(m) for m in self._session.scalars(stmt)]
