# TRACEABILITY — Consolida

Requisito → feature do ROADMAP → critério de verificação. (Versão manipulável em `requisitos.xlsx`, aba Rastreabilidade.)

| Requisito | Feature | Verificação |
|---|---|---|
| FR-001 | F2 | UC-01 pré-cond.; teste de integração register/login |
| FR-002 | F2 | Teste: rota privada sem JWT → 401 |
| FR-003 | F4 | UC-01 cenário "conexão bem-sucedida" |
| FR-004 | F5 | Lista mostra status correto |
| FR-005 | F5 / F9 | UC-04 "consentimento expirado" → reauth |
| FR-006 | F5 / F10 | UC-05 remove conexão e apaga dados |
| FR-007 | F4 / F5 | Sync traz contas e transações |
| FR-008 | F6 | Lista de contas com saldo |
| FR-009 | F8 | RN-02: cartão não soma ao saldo positivo |
| FR-010 | F6 | Lista paginada por conta/período |
| FR-011 | F3 / F6 | Teste de normalização (domínio) |
| FR-012 | F5 / F6 | RN-05: dedupe por chave única |
| FR-013 | F6 | Filtro por texto/valor/categoria/período |
| FR-014 | F7 | Categoria do agregador aplicada |
| FR-015 | F7 | Regra do usuário sobrepõe automática |
| FR-016 | F11 (futuro) | Sugestão por LLM em transação ambígua |
| FR-017 | F7 | UC-03 recategorizar + criar regra |
| FR-018 | F8 | Resumo recebido/gasto/líquido |
| FR-019 | F8 | Gasto por categoria |
| FR-020 | F8 | Evolução mensal |
| FR-021 | F8 (futuro) | Comparativo mês a mês |
| FR-022 | F5 | Sync sob demanda |
| FR-023 | F9 | Sync agendado + webhook |
| FR-024 | F3 | Troca de adapter sem tocar no domínio |
| NFR-001 | F4 / F10 | Segredo cifrado; ausente em logs/resposta |
| NFR-002 | F2 | Sem leitura cross-`user_id` |
| NFR-003 | F10 | Exclusão total de dados sob demanda |
| NFR-004 | F5 | Backoff em 429/529/5xx |
| NFR-005 | F8 | Dashboard ≤ 2 s p95 |
| NFR-006 | F3 | Cobertura domínio ≥ 80%; adapter trocável |
| NFR-007 | F1 / F2 | Índices por `user_id`; sem join cross-tenant |
| NFR-008 | F4 | Conectar em ≤ 3 telas; estados de erro |
| NFR-009 | F9 | Logs estruturados sem PII; métrica de falha |
| NFR-010 | F1 | Sobe via Docker só com env vars |
