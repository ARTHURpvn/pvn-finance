"""Ponto de entrada da API FastAPI do Consolida."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth import router as auth_router
from app.api.errors import error_body
from app.api.health import router as health_router
from app.api.me import router as me_router


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Se o detail já está no envelope padrão, repassa; senão, embrulha.
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            body = exc.detail
        else:
            body = error_body("http_error", str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # NÃO ecoar o valor enviado (`input`) — evitaria vazar senha em
        # respostas/logs (NFR-001). Expomos só tipo, localização e mensagem.
        safe_details = [
            {"type": err.get("type"), "loc": err.get("loc"), "msg": err.get("msg")}
            for err in exc.errors()
        ]
        body = error_body(
            "validation_error",
            "Dados de entrada inválidos",
            details=jsonable_encoder(safe_details),
        )
        return JSONResponse(status_code=422, content=body)


def create_app() -> FastAPI:
    app = FastAPI(title="Consolida API", version="0.1.0")
    _register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(me_router)
    return app


app = create_app()
