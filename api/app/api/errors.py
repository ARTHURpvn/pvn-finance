"""Padronização de erros da API no formato {error:{code,message}} (docs/API.md)."""

from typing import Any

from fastapi import HTTPException, status


def api_error(
    *, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """Cria uma HTTPException já no envelope padrão da API."""
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message}},
    )


def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if extra:
        body["error"].update(extra)
    return body
