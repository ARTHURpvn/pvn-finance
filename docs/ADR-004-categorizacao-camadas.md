# ADR-004 — Categorização em camadas (provider → regras → fallback)

**Status:** Aceito · **Data:** 2026-06

## Contexto
A confiança no "quanto gastei por categoria" depende de categorização boa. O agregador já entrega uma categoria, mas nem sempre acerta o contexto do usuário. LLM resolve casos difíceis, mas tem custo e latência.

## Decisão
Categorizar em camadas, nesta ordem de precedência:
1. **Regra do usuário** (FR-015) — maior prioridade.
2. **Categoria do agregador** (FR-014).
3. **Fallback** "Outros" no MVP; **LLM opcional** (FR-016) adiado para fase futura.

Recategorização manual (FR-017) pode gerar uma regra.

## Consequências
- (+) Determinístico e barato no MVP; melhora com uso (regras).
- (+) LLM entra depois sem mexer no fluxo (só mais uma camada).
- (−) Sem LLM, transações ambíguas caem em "Outros" até o usuário criar regra.
