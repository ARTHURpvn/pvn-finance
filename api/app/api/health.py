"""Healthcheck público (sem auth) — verifica a aplicação e a conexão com o banco."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.infrastructure.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Retorna 200 quando app + banco estão saudáveis; 503 se o banco não responde."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — qualquer falha de DB vira 503
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "db_unavailable", "message": "Banco indisponível"}},
        ) from exc
    return {"status": "ok", "database": "up"}
