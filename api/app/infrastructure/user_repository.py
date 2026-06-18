"""Adapter SQLAlchemy do UserRepository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.user import UserRecord
from app.infrastructure.models import UserModel


class SqlUserRepository:
    """Implementa o port UserRepository sobre SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_record(model: UserModel) -> UserRecord:
        return UserRecord(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
        )

    def add(self, *, email: str, password_hash: str) -> UserRecord:
        model = UserModel(email=email, password_hash=password_hash)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_record(model)

    def get_by_email(self, email: str) -> UserRecord | None:
        stmt = select(UserModel).where(func.lower(UserModel.email) == email.lower())
        model = self._session.scalar(stmt)
        return self._to_record(model) if model else None

    def get_by_id(self, user_id: UUID) -> UserRecord | None:
        model = self._session.get(UserModel, user_id)
        return self._to_record(model) if model else None
