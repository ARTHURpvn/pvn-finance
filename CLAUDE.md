# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

**Consolida** — agregador financeiro pessoal (leitura) via Pluggy (Open Finance). MVP single-user, projetado para virar SaaS multi-tenant.

Stack:
- **Backend:** Python · FastAPI · SQLAlchemy · Alembic (ainda a criar — `api/`)
- **Frontend:** Vite + React 19 + TypeScript + shadcn/ui (`frontend/`)
- **Banco:** PostgreSQL via Docker
- **Dados bancários:** Pluggy atrás de `FinancialDataPort` (Port/Adapter)

## Comandos

### Frontend (`frontend/`)

```bash
npm install          # instalar dependências
npm run dev          # servidor de desenvolvimento (Vite)
npm run build        # tsc -b && vite build
npm run lint         # eslint
npm run preview      # preview do build
```

### Backend (`api/`) — a configurar em F1

```bash
# A definir ao implementar F1. Esperado:
docker compose up -d           # Postgres
uvicorn app.main:app --reload  # FastAPI dev
alembic upgrade head           # migrations
pytest                         # todos os testes
pytest tests/domain/           # apenas testes unitários de domínio
```

## Arquitetura

### Hexagonal (Ports & Adapters)

O domínio não conhece HTTP, Postgres nem Pluggy. O modelo de domínio **espelha o canônico do Open Finance**:

```
Conexão/Consentimento → Conta → Saldo → Transação
```

Camadas do backend:
- **`domain/`** — entidades + regras de negócio (RN-01..05). Zero dependências externas.
- **`application/`** — serviços (`SyncService`, `DashboardService`, `CategorizationService`).
- **`ports/`** — `FinancialDataPort` (interface). Adaptadores implementam esta interface.
- **`adapters/`** — `PluggyAdapter` (MVP); adapter fake para testes.
- **`infrastructure/`** — repositórios SQLAlchemy, cofre de credenciais, worker de sync.
- **`api/`** — rotas FastAPI + auth JWT.

Trocar de agregador = novo adapter implementando `FinancialDataPort`. Núcleo intacto (ADR-002).

### Fluxo de sincronização

1. Gatilho (botão, job agendado ou webhook `/webhooks/pluggy`)
2. `SyncService.sync(connection_id)` → adapter busca contas e transações desde `last_sync_at`
3. Domínio normaliza (RN-01), deduplica por `(connection_id, provider_transaction_id)` (RN-05), aplica categoria (regra → provider → "Outros")
4. Persiste em transação atômica por conta; atualiza `last_sync_at` e status
5. Consentimento expirado → status `requer_reauth` (RN-03)

### Categorização em camadas (ADR-004)

Precedência: **1. Regra do usuário** → **2. Categoria do agregador** → **3. "Outros"** (LLM futura, F11)

### Segurança crítica (ADR-005)

`connections.encrypted_secret` — token do agregador cifrado em repouso (Fernet/AES, chave em env). **Nunca** logar, nunca retornar via API, não incluir em `transactions.raw`.

## Regras de negócio (domínio)

| ID | Regra |
|---|---|
| RN-01 | Sinal de transação: `direction = in` (crédito) / `out` (débito), derivado do sinal do `amount` |
| RN-02 | Cartão de crédito é passivo; excluído do saldo total positivo |
| RN-03 | Consentimento expirado → `connection.status = requer_reauth`; sync não executa |
| RN-04 | Transações imutáveis após import; somente `category_id` pode ser alterado |
| RN-05 | Dedupe por `UNIQUE(connection_id, provider_transaction_id)` |

## Testes

Prioridade: **domínio > contrato do adapter > integração de API**

| Camada | Ferramenta | Meta |
|---|---|---|
| Unitário (domínio) | pytest puro, sem I/O | ≥ 80% de cobertura no domínio |
| Contrato (adapter) | pytest + fixtures de payload Pluggy (sandbox) | — |
| Integração (API) | pytest + Postgres de teste + adapter fake injetado | — |
| Resiliência | Adapter fake simulando 429/529/5xx | — |
| E2E (feliz) | Playwright | — |

Fixture mínima necessária: crédito vs débito, cartão de crédito, transação duplicada, consentimento expirado, transação sem categoria.

## Roadmap de features

Implementar em ordem com `/feature`:

| Feature | Descrição |
|---|---|
| **F1** | Bootstrap: Docker Compose, FastAPI skeleton, SQLAlchemy + Alembic, Vite + shadcn/ui, CI |
| **F2** | Auth: tabela `users`, register/login, JWT, escopo por `user_id` |
| **F3** | Domínio + `FinancialDataPort` + seed de categorias + RN-01/02/04/05 com testes |
| **F4** | `PluggyAdapter` + cofre de credenciais |
| **F5** | CRUD de conexões + `SyncService` + backoff + `sync_logs` |
| **F6** | Listagem de contas com saldo + transações paginadas/filtradas |
| **F7** | Categorização + motor de regras + recategorização manual |
| **F8** | Dashboard (resumo, por categoria, evolução mensal) ≤ 2s p95 |
| **F9** | Worker de sync agendado + webhook `/webhooks/pluggy` |
| **F10** | LGPD: exclusão total de dados + hardening de logs |

## Convenções da API

- Todas as rotas (exceto `/auth/*` e `/webhooks/*`) exigem `Authorization: Bearer <JWT>`
- Toda query filtra por `user_id` — sem leitura cross-tenant
- Erros: `{ "error": { "code", "message" } }`; 429 retorna `Retry-After`
- Datas em ISO-8601; valores monetários como `string` decimal com `currency`
- `transactions.raw` e `connections.encrypted_secret` nunca expostos pela API

## Índices obrigatórios (NFR-005/007)

```sql
UNIQUE (connection_id, provider_transaction_id)
INDEX  transactions (user_id, date)
INDEX  transactions (account_id, date)
INDEX  accounts     (user_id)
INDEX  connections  (user_id)
```

## Documentação de referência

| Arquivo | Conteúdo |
|---|---|
| `docs/ARCHITECTURE.md` | Diagrama de componentes, decisões |
| `docs/DATA_MODEL.md` | ER completo + dicionário de campos |
| `docs/API.md` | Contrato completo da API REST |
| `docs/SRS.md` | Todos os requisitos FR/NFR |
| `docs/ADR-*.md` | Decisões técnicas registradas |
| `docs/TEST_STRATEGY.md` | Estratégia e definição de pronto por feature |
| `docs/ROADMAP.md` | Features detalhadas prontas para `/feature` |
