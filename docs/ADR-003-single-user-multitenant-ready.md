# ADR-003 — Single-user com schema multi-tenant-ready

**Status:** Aceito · **Data:** 2026-06

## Contexto
O MVP é de uso pessoal, mas a meta declarada é virar SaaS. Reescrever para multi-tenant depois é caro e arriscado; já nascer multi-tenant completo (billing, orgs, RBAC) atrasa o MVP.

## Decisão
Modelar **tudo escopado por `user_id`** desde o início (FK + índices + filtro obrigatório em toda query), com um único usuário em uso. Não implementar billing, convites, orgs ou planos agora.

## Consequências
- (+) Virar multi-tenant é "abrir o cadastro" e ligar billing, sem migração estrutural (NFR-007).
- (+) Isolamento por `user_id` já vira teste de segurança (NFR-002).
- (−) Disciplina constante: nenhuma query pode esquecer o filtro `user_id` (cobrir com teste e, se possível, RLS no Postgres no futuro).
