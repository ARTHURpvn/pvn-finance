# Consolida — API

Backend do Consolida (FastAPI · SQLAlchemy · Alembic). Arquitetura hexagonal.

## Dev local (sem Docker)

```bash
uv sync                          # cria venv e instala deps
cp ../.env.example ../.env       # ajuste DATABASE_URL (host: localhost)
uv run alembic upgrade head      # aplica migrations
uv run uvicorn app.main:app --reload
uv run pytest                    # testes
uv run ruff check .              # lint
```

## Com Docker (recomendado)

Na raiz do repositório:

```bash
docker compose up -d             # sobe Postgres + API (roda migrations no boot)
curl localhost:8000/health       # -> {"status":"ok","database":"up"}
```

## Estrutura (hexagonal)

```
app/
  domain/          # entidades + regras de negócio (zero deps externas)
  application/     # serviços de caso de uso
  ports/           # interfaces (FinancialDataPort etc.)
  adapters/        # implementações das ports (Pluggy, fakes)
  infrastructure/  # SQLAlchemy, cofre de credenciais
  api/             # rotas FastAPI
migrations/        # Alembic
tests/             # pytest (domain/ = unitários puros)
```
