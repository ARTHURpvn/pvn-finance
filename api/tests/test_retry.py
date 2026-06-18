"""Backoff/retry (NFR-004)."""

import pytest

from app.application.retry import with_retry
from app.ports.financial_data_port import AggregatorError, RetryableAggregatorError


def test_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RetryableAggregatorError("429")
        return "ok"

    assert with_retry(op, sleep=lambda _d: None) == "ok"
    assert calls["n"] == 3


def test_gives_up_after_max_attempts() -> None:
    def op() -> str:
        raise RetryableAggregatorError("429")

    with pytest.raises(RetryableAggregatorError):
        with_retry(op, max_attempts=2, sleep=lambda _d: None)


def test_non_retryable_raises_immediately() -> None:
    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        raise AggregatorError("fatal")

    with pytest.raises(AggregatorError):
        with_retry(op, sleep=lambda _d: None)
    assert calls["n"] == 1


def test_backoff_delays_are_exponential() -> None:
    delays: list[float] = []

    def op() -> str:
        raise RetryableAggregatorError("429")

    with pytest.raises(RetryableAggregatorError):
        with_retry(op, max_attempts=3, base_delay=0.5, sleep=delays.append)

    assert delays == [0.5, 1.0]  # 0.5*2^0, 0.5*2^1 (sem sleep após última)
