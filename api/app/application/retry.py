"""Retry com backoff exponencial para falhas transitórias do agregador (NFR-004)."""

import time
from collections.abc import Callable

from app.ports.financial_data_port import RetryableAggregatorError


def with_retry[T](
    operation: Callable[[], T],
    *,
    max_attempts: int = 4,
    base_delay: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Executa ``operation``, repetindo em RetryableAggregatorError com backoff
    exponencial (base_delay * 2**n). Erros não-recuperáveis sobem na hora.
    ``sleep`` é injetável para testes (sem espera real)."""
    last_exc: RetryableAggregatorError | None = None
    for attempt in range(max_attempts):
        try:
            return operation()
        except RetryableAggregatorError as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                sleep(base_delay * (2**attempt))
    assert last_exc is not None
    raise last_exc
