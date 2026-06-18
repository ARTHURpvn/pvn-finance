# ADR-005 — Criptografia de credenciais/tokens em repouso

**Status:** Aceito · **Data:** 2026-06

## Contexto
Tokens e segredos do agregador dão acesso a dados financeiros. Vazamento é o pior cenário (RISKS R-04, NFR-001/003).

## Decisão
Cifrar `connections.encrypted_secret` em repouso (Fernet/AES com chave em variável de ambiente ou secret manager; ou `pgcrypto`). Segredos nunca são logados, nunca retornam pela API e ficam fora de `transactions.raw`. Chave de criptografia separada do banco.

## Consequências
- (+) Reduz impacto de dump de banco; alinhado à LGPD.
- (−) Gestão de chave (rotação, backup) vira responsabilidade operacional.
- (~) Considerar Postgres RLS e secret manager gerenciado ao escalar.
