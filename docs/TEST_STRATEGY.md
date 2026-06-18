# TEST_STRATEGY — Consolida

## Princípio
O risco está no **núcleo de domínio** (sinal, saldo consolidado, dedupe, categorização) e na **fronteira com o agregador**. É lá que a cobertura se concentra.

## Camadas

| Camada | O que cobre | Como |
|---|---|---|
| **Unitário (domínio)** | RN-01 sinal · RN-02 saldo consolidado (cartão fora) · RN-05 dedupe · precedência de categorização (ADR-004) | pytest puro, sem I/O. Meta ≥ 80% no domínio (NFR-006). |
| **Contrato (adapter)** | `PluggyAdapter` traduz payload do agregador → domínio | Fixtures de payload reais (sandbox/trial); testa mapeamento e casos de borda. |
| **Integração (API)** | Rotas, auth JWT, escopo por `user_id` (NFR-002) | pytest + Postgres de teste (Docker); adapter fake injetado pela Port. |
| **Resiliência** | Backoff em 429/529/5xx; sync parcial não corrompe (NFR-004) | Adapter fake que simula erros e timeouts. |
| **E2E (feliz)** | Conectar (sandbox) → sync → dashboard | Playwright no frontend contra backend de teste. |
| **Desempenho** | Dashboard ≤ 2 s p95 com 12 meses / 5 contas (NFR-005) | Seed de dados + medição simples. |
| **Segurança** | Sem leitura cross-`user_id`; segredos não vazam em logs/resposta (NFR-001/002) | Testes negativos + checagem de logs. |

## Dados de teste
Fixtures determinísticas de contas/transações cobrindo: crédito vs. débito, cartão de crédito, transação duplicada (mesmo `provider_transaction_id`), consentimento expirado, transação sem categoria.

## Definição de pronto (por feature)
Testes da camada relevante passando, cobertura de domínio mantida ≥ 80%, sem segredo em log, e critério de aceitação Gherkin do caso de uso correspondente verde.
