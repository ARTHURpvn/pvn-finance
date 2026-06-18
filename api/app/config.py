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


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações (cacheadas) — instanciação tardia para testabilidade."""
    return Settings()  # type: ignore[call-arg]
