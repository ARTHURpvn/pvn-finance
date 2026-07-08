"""Adapter SQLAlchemy do RefreshTokenRepository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.infrastructure.models import RefreshTokenModel
from app.ports.refresh_token_repository import RefreshTokenRecord


class SqlRefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_record(model: RefreshTokenModel) -> RefreshTokenRecord:
        return RefreshTokenRecord(
            jti=model.jti,
            user_id=model.user_id,
            family_id=model.family_id,
            revoked=model.revoked,
            expires_at=model.expires_at,
        )

    def add(
        self, *, jti: UUID, user_id: UUID, family_id: UUID, expires_at: datetime
    ) -> None:
        self._session.add(
            RefreshTokenModel(
                jti=jti,
                user_id=user_id,
                family_id=family_id,
                expires_at=expires_at,
            )
        )
        self._session.commit()

    def get(self, jti: UUID) -> RefreshTokenRecord | None:
        model = self._session.get(RefreshTokenModel, jti)
        return self._to_record(model) if model else None

    def revoke(self, jti: UUID) -> None:
        self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(revoked=True)
        )
        self._session.commit()

    def revoke_family(self, family_id: UUID) -> None:
        self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id)
            .values(revoked=True)
        )
        self._session.commit()
