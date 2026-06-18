"""Testes unitários da entidade de domínio User."""

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.user import User, UserRecord


def test_to_public_strips_password_hash() -> None:
    record = UserRecord(
        id=uuid4(),
        email="user@example.com",
        password_hash="argon2$secret",
        created_at=datetime.now(UTC),
    )

    public = record.to_public()

    assert isinstance(public, User)
    assert public.email == record.email
    assert not hasattr(public, "password_hash")
