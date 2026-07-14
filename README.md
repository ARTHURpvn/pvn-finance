# Consolida (PVN Finance)

Agregador financeiro pessoal **read-only** via [Pluggy](https://pluggy.ai) (Open Finance). Conecta suas contas bancárias, consolida saldos, transações e investimentos, e mostra tudo num painel único. MVP single-user, projetado para virar SaaS multi-tenant.

> Arquitetura **hexagonal** (Ports & Adapters): o domínio não conhece HTTP, Postgres nem Pluggy. Trocar de agregador = escrever um novo adapter, sem tocar no núcleo.

## Stack

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.12+ · FastAPI · SQLAlchemy 2 · Alembic · uv |
| **Frontend** | Vite · React 19 · TypeScript · shadcn/ui |
| **Banco** | PostgreSQL 16 (Docker) |
| **Dados bancários** | Pluggy atrás de `FinancialDataPort` (Port/Adapter) |
| **Auth** | JWT (HS256) access + refresh com rotação de família · Argon2 |
| **Segredos** | Fernet/AES para `encrypted_secret` (token do agregador em repouso) |

## Estrutura do repositório

```
.
├── api/            # Backend FastAPI (hexagonal)
│   ├── app/
│   │   ├── domain/          # entidades + regras de negócio (RN-01..05), zero I/O
│   │   ├── application/     # serviços (Sync, Dashboard, Categorization, Auth)
│   │   ├── ports/           # interfaces (FinancialDataPort, repositórios)
│   │   ├── adapters/        # PluggyAdapter + adapter fake para testes
│   │   ├── infrastructure/  # repositórios SQLAlchemy, cofre, segurança, worker
│   │   └── api/             # rotas FastAPI + auth JWT
│   ├── migrations/          # Alembic
│   └── tests/               # 153 testes (domínio > contrato > integração)
├── frontend/       # SPA React (Vite)
├── docs/           # SRS, ADRs, ARCHITECTURE, DATA_MODEL, API, TEST_STRATEGY…
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Como rodar

### Pré-requisitos
- Docker + Docker Compose
- Node.js 24 (frontend)
- [uv](https://docs.astral.sh/uv/) (backend, opcional fora do Docker)

### Backend (Docker)

```bash
cp .env.example .env          # preencha JWT_SECRET, VAULT_KEY, PLUGGY_* etc.
docker compose up -d db api   # sobe Postgres + API (roda migrations no boot)
```

A API sobe na porta definida por `API_PORT` (default `8000`). Health: `GET /health`.

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

O frontend aponta para `VITE_API_URL` (default `http://localhost:8000`). Configure em `frontend/.env` se a API estiver em outra porta.

### Variáveis de ambiente

| Var | Onde | Descrição |
|---|---|---|
| `DATABASE_URL` | api | conexão Postgres (`postgresql+psycopg://…`) |
| `JWT_SECRET` | api | segredo de assinatura dos tokens (nunca commitar) |
| `VAULT_KEY` | api | chave Fernet do cofre de credenciais |
| `PLUGGY_CLIENT_ID` / `PLUGGY_CLIENT_SECRET` | api | credenciais do agregador |
| `API_PORT` / `DB_PORT` | compose | portas publicadas no host |
| `VITE_API_URL` | frontend | URL base da API |

`.env` e `.env.local` são gitignorados. Use `.env.example` como referência (sem valores reais).

---

## Deploy (produção / VPS)

Um comando sobe a stack inteira (Postgres + API + worker + frontend) numa VPS com Docker:

```bash
./deploy.sh
```

O script (`deploy.sh` + `docker-compose.prod.yml`):
- cria o `.env` a partir do `.env.example` na primeira execução;
- **gera segredos fortes** (`JWT_SECRET`, `VAULT_KEY` Fernet, `POSTGRES_PASSWORD`) se ainda forem os placeholders — e não os regenera depois;
- faz build e sobe tudo; as **migrations rodam no boot** da API;
- espera a API ficar saudável e mostra o status.

**HTTPS automático:** defina `DOMAIN=seu.dominio.com` no `.env` (DNS apontando para o servidor, portas 80/443 abertas) e rode de novo — o [Caddy](https://caddyserver.com) emite e renova o certificado sozinho. Sem `DOMAIN`, serve em HTTP na porta 80.

**Arquitetura de produção:** só o serviço `web` (Caddy) fica exposto — ele serve o SPA e faz proxy de `/api/*` para a API (mesma origem, sem CORS). Postgres e API ficam na rede interna do compose. O `VITE_API_URL` é embutido como `/api` no build.

```bash
docker compose -f docker-compose.prod.yml logs -f   # logs
docker compose -f docker-compose.prod.yml down       # derrubar
```

---

## Testes e CI

O pipeline roda em **todo push na `main` e em todo pull request** (`.github/workflows/ci.yml`), em **dois jobs paralelos**:

### Job `backend`
Sobe um Postgres 16 de serviço e executa, em ordem (falha em qualquer passo reprova o PR):

| # | Passo | Comando | O que garante |
|---|---|---|---|
| 1 | Deps | `uv sync --frozen` | ambiente reproduzível (lock travado) |
| 2 | **Lint** | `ruff check .` | estilo e erros estáticos no Python |
| 3 | **Migrations** | `alembic upgrade head` | todas as migrations aplicam num banco limpo |
| 4 | **Testes** | `pytest --cov=app/domain --cov-fail-under=80` | 153 testes passam **e** cobertura do domínio ≥ 80% (hoje 99%) |

### Job `frontend`

| # | Passo | Comando | O que garante |
|---|---|---|---|
| 1 | Deps | `npm install` | instala dependências |
| 2 | **Lint** | `npm run lint` (eslint) | estilo e erros estáticos no TS/React |
| 3 | **Build** | `npm run build` (`tsc -b && vite build`) | type-check completo + build de produção sem erro |

> ⚠️ O frontend **não tem testes automatizados** hoje — só lint + build. Ver a checklist abaixo para a decisão de adicionar (Vitest/Playwright).

### O que cada suíte de testes cobre

**153 testes**, organizados por camada (prioridade da estratégia: **domínio > contrato do adapter > integração de API** — ver [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md)). As contagens abaixo são de casos coletados pelo pytest (parametrizações expandem cada `def` em vários casos).

#### Domínio — unitário, pytest puro, **sem I/O** (54 testes)
Validam as regras de negócio em memória, com asserts diretos sobre as entidades.

| Arquivo | Nº | Cobre |
|---|---|---|
| `domain/test_connection.py` | 15 | **RN-03** — expiração de consentimento → `requer_reauth` |
| `domain/test_investment.py` | 12 | investimentos no patrimônio, reserva vs. prazo, flag `is_transfer` |
| `domain/test_categorization.py` | 8 | motor de categorização em camadas (ADR-004) + `Rule.matches` |
| `domain/test_transaction.py` | 7 | **RN-01** (sinal in/out pelo `amount`) e **RN-04** (transação imutável após import) |
| `domain/test_account.py` | 3 | **RN-02** — saldo consolidado exclui cartão de crédito do total positivo |
| `domain/test_dedupe.py` | 3 | **RN-05** — dedupe por `(connection_id, provider_transaction_id)` |
| `domain/test_category.py` | 3 | taxonomia de categorias de sistema (seed) |
| `domain/test_rule.py` | 2 | entidade `Rule` (regra do usuário) |
| `domain/test_user.py` | 1 | entidade `User` |

#### Aplicação (5 testes)
| Arquivo | Nº | Cobre |
|---|---|---|
| `application/test_normalization.py` | 5 | normalização provider → domínio (sinal do cartão invertido, `is_transfer` de aplicações/transferências próprias) |

#### Contrato do adapter — pytest + fixtures de payload, **sem rede** (11 testes)
| Arquivo | Nº | Cobre |
|---|---|---|
| `adapters/test_pluggy.py` | 10 | contrato do `PluggyAdapter`: mapeamento de payloads Pluggy → entidades |
| `adapters/test_fake.py` | 1 | adapter fake do `FinancialDataPort` (usado nos testes de integração) |

#### Integração de API — pytest + FastAPI `TestClient` + Postgres de teste + adapter fake injetado (56 testes)
| Arquivo | Nº | Cobre |
|---|---|---|
| `test_auth_api.py` | 15 | register / login / **refresh** / logout (CA-1..CA-9), rotação de token |
| `test_webhook_api.py` | 10 | webhook `/webhooks/pluggy` (F9): auth por header, idempotência, reconciliação |
| `test_connections_api.py` | 7 | CRUD de conexões (F5) com adapter fake |
| `test_accounts_transactions_api.py` | 6 | listagem de contas + transações paginadas/filtradas (F6) |
| `test_categorization_api.py` | 6 | categorias, motor de regras, recategorização manual (F7) |
| `test_dashboard_api.py` | 6 | agregações do dashboard: resumo, por categoria, evolução (F8) |
| `test_health.py` | 2 | `GET /health` (CA-2), sem dependência de banco |
| `test_lgpd_hardening.py` | 3 | exclusão total de dados (LGPD, F10) + rate limit em `/auth/*` |
| `test_categories_seed.py` | 1 | seed de categorias aplicado pela migration |

#### Serviços e infraestrutura — pytest + Postgres/fakes (27 testes)
| Arquivo | Nº | Cobre |
|---|---|---|
| `test_sync_service.py` | 8 | `SyncService`: busca, normaliza, deduplica, persiste; atualiza `last_sync_at` |
| `test_scheduler.py` | 2 | varredura de sync agendada (F9) |
| `test_retry.py` | 6 | backoff/retry em 429/5xx (NFR-004) |
| `test_scale_indexes.py` | 3 | migration 0007 criou os índices de escala e removeu o redundante (F4) |
| `test_security.py` | 5 | primitivas de segurança: hash Argon2, emissão/decodificação de JWT |
| `test_vault.py` | 3 | cofre de credenciais Fernet (ADR-005): cifra/decifra, nunca vaza segredo |

---

## Checklist — quais checks manter no CI

Marque `[x]` no que deve **continuar** rodando e desmarque `[ ]` o que quer **remover**. Cada item traz o custo/benefício da decisão.

### Gates do pipeline

- [x] **backend · lint (ruff)** — barato, pega erro estático. Remover só se for migrar de linter.
- [x] **backend · migrations (alembic upgrade head)** — garante que o schema aplica do zero; crítico p/ deploy.
- [x] **backend · testes (pytest)** — a rede de segurança do backend.
- [x] **backend · gate de cobertura ≥ 80% no domínio** (`--cov-fail-under=80`) — força cobrir regra de negócio nova. Remover = PRs passam mesmo com domínio descoberto.
- [x] **frontend · lint (eslint)** — barato, pega erro estático.
- [x] **frontend · build (tsc + vite)** — type-check completo; pega erro de tipo antes do deploy.
- [ ] **frontend · testes automatizados** — **não existe hoje.** Marque se quiser que eu adicione Vitest (unit/componentes) e/ou Playwright (E2E do fluxo feliz).

### Suítes de teste do backend (todas passam hoje)

**Domínio (54) — recomendo manter todas; são a base do gate de cobertura:**
- [x] `test_transaction.py` — RN-01/RN-04
- [x] `test_account.py` — RN-02
- [x] `test_dedupe.py` — RN-05
- [x] `test_connection.py` — RN-03
- [x] `test_categorization.py` — ADR-004
- [x] `test_category.py` — seed de categorias
- [x] `test_rule.py` — entidade Rule
- [x] `test_investment.py` — patrimônio/investimentos
- [x] `test_user.py` — entidade User

**Aplicação / Adapters:**
- [x] `application/test_normalization.py` — normalização provider→domínio
- [x] `adapters/test_pluggy.py` — contrato Pluggy (sem rede)
- [x] `adapters/test_fake.py` — adapter fake

**Integração de API:**
- [x] `test_auth_api.py` — auth + refresh
- [x] `test_health.py` — healthcheck
- [x] `test_connections_api.py` — conexões (F5)
- [x] `test_accounts_transactions_api.py` — contas/transações (F6)
- [x] `test_categorization_api.py` — categorias/regras (F7)
- [x] `test_dashboard_api.py` — dashboard (F8)
- [x] `test_webhook_api.py` — webhook Pluggy (F9)
- [x] `test_lgpd_hardening.py` — LGPD + rate limit (F10)
- [x] `test_categories_seed.py` — seed via migration

**Serviços / Infra:**
- [x] `test_sync_service.py` — SyncService
- [x] `test_scheduler.py` — sync agendado (F9)
- [x] `test_retry.py` — backoff/retry (NFR-004)
- [x] `test_scale_indexes.py` — índices de escala (F4)
- [x] `test_security.py` — Argon2 + JWT
- [x] `test_vault.py` — cofre de credenciais (ADR-005)

> Rodar um subconjunto localmente:
> ```bash
> cd api
> uv run pytest tests/domain/            # só o domínio
> uv run pytest tests/test_auth_api.py   # só um arquivo
> uv run pytest -k webhook               # por palavra-chave
> ```

---

## Documentação de referência

| Arquivo | Conteúdo |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diagrama de componentes e decisões |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | ER completo + dicionário de campos |
| [docs/API.md](docs/API.md) | Contrato REST completo |
| [docs/SRS.md](docs/SRS.md) | Requisitos FR/NFR |
| [docs/TEST_STRATEGY.md](docs/TEST_STRATEGY.md) | Estratégia de testes e definição de pronto |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Features F1–F10 detalhadas |
| [docs/ADR-*.md](docs/) | Decisões técnicas registradas |

## Convenções

- Rotas (exceto `/auth/*` e `/webhooks/*`) exigem `Authorization: Bearer <JWT>`.
- Toda query filtra por `user_id` — sem leitura cross-tenant.
- Erros: `{ "error": { "code", "message" } }`; 429 retorna `Retry-After`.
- Datas em ISO-8601; valores monetários como `string` decimal com `currency`.
- `transactions.raw` e `connections.encrypted_secret` **nunca** são expostos pela API.
- Commits em [Conventional Commits](https://www.conventionalcommits.org/) (PT-BR); branches `feature/`, `fix/`, `chore/`; PRs contra `main`.
