"""Configuração de testes.

Defaults inócuos de ambiente para os testes unitários (que não tocam o
banco). Os testes que usam DB pedem a fixture `_schema`/`db_session`/`client`,
que aplicam as migrations reais (Alembic) num Postgres acessível via
DATABASE_URL — assim o seed de categorias também é exercitado.
"""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://consolida:consolida@localhost:5432/consolida",
)
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod-0123456789")
os.environ.setdefault("VAULT_KEY", "gNJ16n_LeMvqKdM_Fzseu-F548qW99DlkFjjAgSezSY=")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import app.infrastructure.models  # noqa: E402,F401 — registra modelos no metadata
from app.infrastructure.db import get_sessionmaker  # noqa: E402
from app.infrastructure.models import UserModel  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _schema() -> Iterator[None]:
    """Aplica as migrations no banco de teste e reverte ao final."""
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Isola o rate limiter in-memory entre testes."""
    from app.api.rate_limit import get_auth_limiter

    get_auth_limiter().clear()


@pytest.fixture
def db_session(_schema) -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session


@pytest.fixture
def client(_schema) -> TestClient:
    """TestClient com a tabela users limpa antes de cada teste."""
    with get_sessionmaker()() as session:
        session.query(UserModel).delete()
        session.commit()
    return TestClient(app)
