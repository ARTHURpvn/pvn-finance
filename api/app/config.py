"""Configuração 12-factor via variáveis de ambiente (NFR-010)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação carregada do ambiente.

    Campos sem default são obrigatórios: a ausência faz a aplicação
    falhar no startup com erro explícito (CA-4 / 12-factor).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    app_env: str = "development"

    # Autenticação / JWT (F2)
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_minutes: int = 60 * 24 * 30  # 30 dias

    # Cofre de credenciais (F4 / ADR-005) — chave Fernet, separada do banco.
    vault_key: str

    # Agregador Pluggy (F4) — opcionais; app sobe sem eles.
    pluggy_client_id: str | None = None
    pluggy_client_secret: str | None = None
    pluggy_base_url: str = "https://api.pluggy.ai"

    # CORS — origens permitidas (csv) ou "*". Em produção, restrinja.
    cors_origins: str = "*"

    # Webhook do Pluggy (F9) — segredo p/ validar assinatura HMAC (opcional).
    pluggy_webhook_secret: str | None = None

    # Worker de sync agendado (F9)
    sync_interval_minutes: int = 60  # intervalo entre varreduras
    sync_stale_minutes: int = 60  # conexão é "devida" se sync mais antigo que isso


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações (cacheadas) — instanciação tardia para testabilidade."""
    return Settings()  # type: ignore[call-arg]
