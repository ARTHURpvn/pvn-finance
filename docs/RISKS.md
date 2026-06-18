# RISKS — Consolida

Probabilidade × Impacto × Mitigação. (Versão manipulável em `requisitos.xlsx`, aba Riscos.)

| ID | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| R-01 | Custo fixo do agregador inviabiliza a unit economics do SaaS | Alta | Alto | Começar no trial; modelar preço por usuário cobrindo o fixo; reavaliar agregador mais barato (QA-01) |
| R-02 | Lock-in no Pluggy | Média | Médio | Port/Adapter (ADR-002); domínio espelha Open Finance |
| R-03 | Mudança regulatória (modelo 1x1x1 do BC) altera enquadramento de "parceria" | Média | Alto | Acompanhar normas; o agregador absorve a maior parte do impacto; manter consentimento explícito |
| R-04 | Vazamento de dados financeiros (LGPD) | Baixa | Altíssimo | Criptografia em repouso (ADR-005); escopo por finalidade; exclusão sob demanda; sem PII em log |
| R-05 | Consentimento expira e usuário não reautentica → dados desatualizados | Alta | Médio | Estado `requer_reauth` claro + aviso + reauth em poucos cliques (RN-03) |
| R-06 | Rate limit / instabilidade do agregador | Média | Médio | Backoff exponencial; sync incremental; tratar 429/529 (NFR-004) |
| R-07 | Falha de dedupe infla totais | Média | Médio | Chave única `(connection_id, provider_transaction_id)` (RN-05) + teste |
| R-08 | Categorização ruim mina a confiança no "quanto gastei" | Média | Médio | Regras do usuário + recategorização (ADR-004); LLM como evolução |
| R-09 | Query esquece filtro `user_id` (vazamento entre tenants) | Média | Alto | Repositório central com filtro obrigatório; teste de segurança; RLS futuro |
