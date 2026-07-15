"""Ponto de entrada da API FastAPI do Consolida."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from app.api.accounts import router as accounts_router
from app.api.auth import router as auth_router
from app.api.categories import router as categories_router
from app.api.connections import router as connections_router
from app.api.dashboard import router as dashboard_router
from app.api.errors import error_body
from app.api.health import router as health_router
from app.api.investments import router as investments_router
from app.api.me import router as me_router
from app.api.rules import router as rules_router
from app.api.subscriptions import router as subscriptions_router
from app.api.transactions import router as transactions_router
from app.api.webhooks import router as webhooks_router
from app.config import get_settings
from app.logging_config import setup_logging


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Se o detail já está no envelope padrão, repassa; senão, embrulha.
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            body = exc.detail
        else:
            body = error_body("http_error", str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content=body,
            headers=getattr(exc, "headers", None),
        )

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


def _configure_cors(app: FastAPI) -> None:
    settings = get_settings()
    raw = settings.cors_origins.strip()
    origins = ["*"] if raw == "*" else [o.strip() for o in raw.split(",") if o.strip()]
    if settings.app_env == "production" and "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS não pode ser '*' em produção — defina as origens permitidas."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Consolida API", version="0.1.0")
    # Comprime respostas > 1KB (extrato, dashboard) — ganho grande em JSON.
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    _configure_cors(app)
    _register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(connections_router)
    app.include_router(accounts_router)
    app.include_router(transactions_router)
    app.include_router(categories_router)
    app.include_router(rules_router)
    app.include_router(dashboard_router)
    app.include_router(investments_router)
    app.include_router(subscriptions_router)
    app.include_router(webhooks_router)
    return app


app = create_app()
