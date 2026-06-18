"""Rate limiting simples (in-memory) para /auth/* (F10).

Janela deslizante por (IP, rota). In-memory atende o MVP single-instance;
ao escalar horizontalmente, trocar por Redis."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.api.errors import error_body
from app.config import get_settings


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def clear(self) -> None:
        self._hits.clear()

    def hit(self, key: str, now: float) -> float | None:
        """Registra um acesso. Retorna None se permitido, ou os segundos de
        ``Retry-After`` se o limite foi excedido."""
        bucket = self._hits[key]
        while bucket and now - bucket[0] >= self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_attempts:
            return max(1.0, self.window_seconds - (now - bucket[0]))
        bucket.append(now)
        return None


_limiter: RateLimiter | None = None


def get_auth_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        settings = get_settings()
        _limiter = RateLimiter(
            settings.auth_rate_limit_max, settings.auth_rate_limit_window_seconds
        )
    return _limiter


def auth_rate_limit(request: Request) -> None:
    limiter = get_auth_limiter()
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    retry_after = limiter.hit(key, time.monotonic())
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_body(
                "rate_limited", "Muitas tentativas. Tente novamente em instantes."
            ),
            headers={"Retry-After": str(int(retry_after))},
        )
