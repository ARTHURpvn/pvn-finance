"""Deduplicação de transações (RN-05).

A chave canônica é ``(connection_id, provider_transaction_id)``. Como a
deduplicação ocorre no escopo de uma conexão durante o sync, basta o
``provider_transaction_id`` aqui; a unicidade no banco é garantida por
``UNIQUE(connection_id, provider_transaction_id)`` (F5)."""

from collections.abc import Iterable

from app.domain.transaction import Transaction


def dedupe_by_provider_id(
    transactions: Iterable[Transaction],
    *,
    existing_provider_ids: Iterable[str] = (),
) -> list[Transaction]:
    """Remove transações repetidas por ``provider_transaction_id``.

    ``existing_provider_ids`` representa o que já foi persistido em syncs
    anteriores; itens com esses ids são descartados. Dentro do lote,
    mantém a primeira ocorrência."""
    seen: set[str] = set(existing_provider_ids)
    result: list[Transaction] = []
    for transaction in transactions:
        if transaction.provider_transaction_id in seen:
            continue
        seen.add(transaction.provider_transaction_id)
        result.append(transaction)
    return result
