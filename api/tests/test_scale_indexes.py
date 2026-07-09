"""Índices de escala (F4) — confirma que a migration 0007 criou os índices
esperados e removeu o redundante."""

from sqlalchemy import inspect
from sqlalchemy.orm import Session


def _index_names(session: Session, table: str) -> set[str]:
    return {i["name"] for i in inspect(session.bind).get_indexes(table)}


def test_transactions_scale_indexes_present(db_session: Session) -> None:
    idx = _index_names(db_session, "transactions")
    assert "ix_transactions_description_trgm" in idx  # busca ILIKE (pg_trgm)
    assert "ix_transactions_user_category_date" in idx  # filtro por categoria


def test_connections_partial_index_present(db_session: Session) -> None:
    assert "ix_connections_due" in _index_names(db_session, "connections")


def test_redundant_accounts_index_removed(db_session: Session) -> None:
    # coberto pelo prefixo de uq_accounts_connection_provider
    assert "ix_accounts_connection_id" not in _index_names(db_session, "accounts")
