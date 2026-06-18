# API — Consolida (API interna)

REST/JSON. Todas as rotas (exceto `/auth/*` e `/webhooks/*`) exigem `Authorization: Bearer <JWT>` e são escopadas por `user_id`. Listas usam paginação `?page=&page_size=`.

## Auth
| Método | Rota | Descrição | FR |
|---|---|---|---|
| POST | `/auth/register` | Cria usuário (201; nunca retorna senha/hash) | FR-001 |
| POST | `/auth/login` | Retorna `access_token` + `refresh_token` (JWT) | FR-002 |
| POST | `/auth/refresh` | Troca um `refresh_token` válido por novo `access_token` | FR-002 |
| GET | `/me` | Dados do usuário autenticado (rota privada de exemplo) | FR-002 |
| DELETE | `/me` | Exclui o usuário e todos os seus dados (LGPD) | FR-006, NFR-003 |

## Conexões
| Método | Rota | Descrição | FR |
|---|---|---|---|
| POST | `/connections` | Inicia conexão; retorna token/URL do widget do agregador | FR-003 |
| POST | `/connections/register` | Registra a conexão após o widget (recebe `provider_item_id`) | FR-003 |
| GET | `/connections` | Lista conexões com status | FR-004 |
| GET | `/connections/{id}` | Detalhe de uma conexão | FR-004 |
| POST | `/connections/{id}/sync` | Dispara sync sob demanda | FR-007, FR-022 |
| POST | `/connections/{id}/reauth` | Reinicia consentimento | FR-005 |
| DELETE | `/connections/{id}` | Revoga e apaga dados associados | FR-006, NFR-003 |

## Contas
| Método | Rota | Descrição | FR |
|---|---|---|---|
| GET | `/accounts` | Lista contas com saldo | FR-008 |
| GET | `/accounts/{id}` | Detalhe da conta | FR-008 |

## Transações
| Método | Rota | Descrição | FR |
|---|---|---|---|
| GET | `/transactions?account_id=&from=&to=&category_id=&q=` | Lista filtrada/paginada | FR-010, FR-013 |
| PATCH | `/transactions/{id}` | Recategoriza (`{category_id, create_rule?}`) | FR-017 |

## Categorias e regras
| Método | Rota | Descrição | FR |
|---|---|---|---|
| GET | `/categories` | Lista categorias (sistema + usuário) | FR-014 |
| POST | `/categories` | Cria categoria | FR-014 |
| GET | `/rules` | Lista regras | FR-015 |
| POST | `/rules` | Cria regra | FR-015 |
| DELETE | `/rules/{id}` | Remove regra | FR-015 |

## Dashboard
| Método | Rota | Descrição | FR |
|---|---|---|---|
| GET | `/dashboard/summary?from=&to=` | Total recebido, gasto, líquido | FR-018 |
| GET | `/dashboard/by-category?from=&to=` | Gasto por categoria | FR-019 |
| GET | `/dashboard/timeline?from=&to=` | Evolução mensal in/out | FR-020 |

## Webhook (agregador)
| Método | Rota | Descrição | FR |
|---|---|---|---|
| POST | `/webhooks/pluggy` | Recebe notificação de mudança; valida assinatura; dispara sync incremental | FR-023 |

## Convenções

- Erros: corpo `{ "error": { "code", "message" } }`; `429` com `Retry-After` quando o agregador limita.
- Datas em ISO-8601; valores monetários em `numeric` (string decimal), com `currency`.
- Nunca retornar `encrypted_secret` nem `transactions.raw` cru.
