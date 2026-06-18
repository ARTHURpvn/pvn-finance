"""Configuração de testes.

Defaults inócuos de ambiente para os testes unitários (que não tocam o
banco). Os testes de API usam a fixture `client`, que cria o schema e
exige um Postgres acessível via DATABASE_URL.
"""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://consolida:consolida@localhost:5432/consolida",
)
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod-0123456789")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.infrastructure.models  # noqa: E402,F401 — registra modelos no metadata
from app.infrastructure.db import Base, get_engine, get_sessionmaker  # noqa: E402
from app.infrastructure.models import UserModel  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _schema():
    """Cria o schema no banco de teste (somente para testes que usam DB)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(_schema) -> TestClient:
    """TestClient com a tabela users limpa antes de cada teste."""
    with get_sessionmaker()() as session:
        session.query(UserModel).delete()
        session.commit()
    return TestClient(app)
