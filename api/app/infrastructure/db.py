"""Infraestrutura de banco — engine/sessão SQLAlchemy e base declarativa.

O domínio NÃO importa este módulo (regra hexagonal). Apenas as camadas
de infraestrutura/aplicação dependem daqui.
"""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos ORM (schema definido a partir da F2/F3)."""


def get_engine() -> Engine:
    """Engine singleton, criada sob demanda a partir do DATABASE_URL."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,  # descarta conexões mortas antes de usar
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_recycle=settings.db_pool_recycle_seconds,
        )
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory


def get_session() -> Iterator[Session]:
    """Dependency FastAPI: fornece uma sessão por request e a fecha ao final."""
    with get_sessionmaker()() as session:
        yield session
