# ROADMAP — Consolida

Features na ordem de construção (respeitando dependências). Cada uma é um brief pronto pra `/feature` — o `/feature` clarifica o detalhe fino.

---

## F1 — Bootstrap & infra
**Depende de:** nada. **Cobre:** NFR-007, NFR-010.
Repo, Docker Compose (Postgres), FastAPI skeleton, SQLAlchemy + Alembic, config 12-factor por env, skeleton Vite + React + TS + shadcn/ui. Healthcheck. CI rodando lint + testes.

## F2 — Auth & usuário
**Depende de:** F1. **Cobre:** FR-001, FR-002, NFR-002.
Tabela `users`, register/login, hash de senha, JWT, dependency de auth nas rotas privadas, escopo por `user_id`. Teste: rota privada sem token → 401.

## F3 — Domínio + Port do provedor
**Depende de:** F2. **Cobre:** FR-011, FR-024, NFR-006.
Entidades de domínio espelhando Open Finance (Conexão, Conta, Transação, Categoria, Regra), `FinancialDataPort`, categorias de sistema (seed), normalização e regras RN-01/02/04/05 com testes unitários (meta ≥ 80%).

## F4 — Adapter Pluggy + cofre de credenciais
**Depende de:** F3. **Cobre:** FR-003, FR-007, NFR-001, NFR-008.
`PluggyAdapter` implementando a Port; emissão do connect token/URL do widget; troca/refresh de token; cofre cifrado (ADR-005). Conectar em ≤ 3 telas. Teste de contrato com fixtures.

## F5 — Conexões: CRUD + sync
**Depende de:** F4. **Cobre:** FR-004, FR-005, FR-006, FR-007, FR-012, FR-022, NFR-004, RN-03, RN-05.
Endpoints de conexão; `SyncService` (sob demanda); dedupe; estados `ativa/requer_reauth/erro`; backoff em 429/529/5xx; `sync_logs`.

## F6 — Contas & transações
**Depende de:** F5. **Cobre:** FR-008, FR-010, FR-011, FR-013.
Listagem de contas com saldo; listagem paginada e filtrada de transações; normalização consolidada.

## F7 — Categorização
**Depende de:** F6. **Cobre:** FR-014, FR-015, FR-017, ADR-004, RN-04.
Categoria do agregador; motor de regras do usuário (precedência); recategorização manual + criar regra a partir dela.

## F8 — Dashboard
**Depende de:** F7. **Cobre:** FR-018, FR-019, FR-020, RN-01, RN-02, NFR-005.
Resumo recebido/gasto/líquido; gasto por categoria; evolução mensal. Cartão fora do saldo positivo. ≤ 2 s p95.

## F9 — Sync agendado + webhook
**Depende de:** F5. **Cobre:** FR-023, NFR-009, R-05, R-06.
Worker periódico; receptor `/webhooks/pluggy` com validação de assinatura; logs estruturados sem PII; métrica de falha por adapter.

## F10 — LGPD & hardening
**Depende de:** F5. **Cobre:** FR-006, NFR-001, NFR-003.
Exclusão total de dados do usuário (direito ao esquecimento); revisão de logs (sem PII/segredo); checklist de segurança.

---

## Futuro (pós-MVP)
- **F11 — Categorização por LLM** (FR-016, QA-02).
- **F12 — Multi-tenant completo + billing** (QA-01): cadastro aberto, planos, cobrança cobrindo o custo do agregador.
- **F13 — Investimentos/crédito** (QA-03): novos escopos do Grupo DC.

**Próximo passo:** rodar F1 → F10 em ordem com `/feature`.
