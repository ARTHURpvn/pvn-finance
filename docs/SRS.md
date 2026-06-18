# SRS — Consolida

Especificação de requisitos. Toda linha tem ID e é verificável. Prioridade **MoSCoW** (Must / Should / Could / Won't-now).

## 1. Contexto

Agregador financeiro pessoal, leitura-only, que consome dados bancários via agregador certificado (Pluggy no MVP) atrás de uma camada Port/Adapter. O domínio espelha o modelo canônico do Open Finance (Conta → Saldo → Transação; Conexão/Consentimento), de modo que trocar de agregador — ou plugar o Open Finance direto no futuro — não reescreva o núcleo.

## 2. Requisitos Funcionais (FR)

### Autenticação e usuário
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-001 | Cadastro e login de usuário; todo dado é escopado por `user_id` | Must |
| FR-002 | Sessão autenticada via JWT em todas as rotas privadas | Must |

### Conexão bancária (via agregador)
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-003 | Iniciar conexão de um banco pelo fluxo do agregador (widget Pluggy Connect), criando uma Conexão | Must |
| FR-004 | Listar conexões do usuário com status (`ativa`, `requer_reauth`, `erro`) | Must |
| FR-005 | Reautenticar/atualizar uma conexão existente | Should |
| FR-006 | Remover/revogar uma conexão e seus dados associados | Must |
| FR-007 | Sincronizar contas e transações de uma conexão (pull do agregador) | Must |

### Contas e saldos
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-008 | Listar contas agregadas (corrente, poupança, pagamento, cartão) com saldo atual | Must |
| FR-009 | Exibir saldo consolidado por usuário e por tipo de conta (ver RN-02) | Must |

### Transações
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-010 | Listar transações por conta e período, com paginação | Must |
| FR-011 | Normalizar transações ao modelo de domínio (data, valor, sinal, descrição, contraparte) | Must |
| FR-012 | Deduplicar transações em sincronizações repetidas (ver RN-05) | Must |
| FR-013 | Buscar/filtrar transações por texto, valor, categoria e período | Should |

### Categorização
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-014 | Atribuir categoria a cada transação, usando a categoria do agregador quando disponível | Must |
| FR-015 | Motor de regras do usuário (ex.: descrição contém "iFood" → Alimentação) sobrepõe a categoria automática | Should |
| FR-016 | Sugerir categoria por heurística/LLM quando não houver regra nem categoria do agregador | Could |
| FR-017 | Recategorizar manualmente uma transação, com opção de gerar regra a partir dela | Should |

### Dashboard / insights
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-018 | Resumo do período: total recebido, total gasto, saldo líquido | Must |
| FR-019 | Gasto por categoria (gráfico) no período | Must |
| FR-020 | Evolução mensal de entradas e saídas | Should |
| FR-021 | Comparativo mês a mês | Could |

### Sincronização
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-022 | Sincronização sob demanda (botão "atualizar") | Must |
| FR-023 | Sincronização agendada (job periódico), respeitando rate limits e defasagem de dados | Should |

### Abstração de provedor
| ID | Requisito | MoSCoW |
|---|---|---|
| FR-024 | Camada Port/Adapter: o domínio não conhece Pluggy; o adapter Pluggy implementa a Port e é substituível | Must |

## 3. Requisitos Não-Funcionais (NFR) — ISO/IEC 25010

| ID | Atributo | Requisito verificável |
|---|---|---|
| NFR-001 | Segurança | Credenciais/tokens do agregador criptografados em repouso; nunca aparecem em logs nem em respostas da API |
| NFR-002 | Segurança | Toda rota privada autenticada; consultas filtram por `user_id` (sem leitura cross-tenant), validado por teste |
| NFR-003 | Privacidade (LGPD) | Usuário pode revogar conexões e excluir 100% dos seus dados sob demanda; dados usados só para a finalidade declarada |
| NFR-004 | Confiabilidade | Sync trata HTTP 429/529/5xx com backoff exponencial; falha parcial não corrompe estado (transação de banco atômica por conta) |
| NFR-005 | Desempenho | Dashboard responde em ≤ 2 s (p95) com 12 meses de transações de até 5 contas |
| NFR-006 | Manutenibilidade | Trocar de agregador exige implementar apenas um novo adapter; cobertura de testes do núcleo de domínio ≥ 80% |
| NFR-007 | Escalabilidade | Schema/queries prontos para multi-tenant (índices por `user_id`, sem joins entre tenants) |
| NFR-008 | Usabilidade | Conectar um banco em ≤ 3 telas; estados de erro e de reautenticação explícitos |
| NFR-009 | Observabilidade | Logs estruturados de sync sem PII; métrica de taxa de falha por adapter |
| NFR-010 | Portabilidade | Backend e Postgres em Docker; configuração 100% por variáveis de ambiente (12-factor) |

## 4. Regras de Negócio (RN)

- **RN-01** — Sinal: crédito = entrada (+), débito = saída (−). "Recebi/gastei" derivam do sinal.
- **RN-02** — Saldo consolidado = soma dos saldos de contas ativas; **cartão de crédito não soma como saldo positivo** (é passivo/fatura, exibido à parte).
- **RN-03** — Conexão/consentimento tem validade; ao expirar entra em `requer_reauth` e para de sincronizar (consentimento de dados no Open Finance dura no máximo 12 meses).
- **RN-04** — Transação é imutável após importada; recategorizar altera só a categoria, preservando origem e histórico.
- **RN-05** — Deduplicação pela chave única `(connection_id, provider_transaction_id)`.

## 5. Restrições

- **RES-01** — Acesso a dados reais só via agregador certificado (Pluggy no MVP). Não há acesso direto às APIs reguladas do Open Finance sem ser instituição autorizada pelo BC (ver ADR-001).
- **RES-02** — Stack: Python/FastAPI + SQLAlchemy + Alembic; Vite + React + TypeScript + shadcn/ui; PostgreSQL em Docker.
- **RES-03** — MVP web-first, single-user, leitura apenas (sem iniciação de pagamento).

## 6. Premissas

- **PRE-01** — O agregador entrega contas, saldos, transações e categoria já normalizados via API; o trial cobre o desenvolvimento.
- **PRE-02** — Em produção o custo do agregador é um fixo mensal (impacta a unit economics do SaaS — ver RISKS R-01).
- **PRE-03** — O consentimento do banco é obtido pelo fluxo do agregador (Pluggy Connect), fora do nosso código.

## 7. Questões em aberto

- **QA-01** — Modelo de monetização do SaaS (preço por usuário vs. limites de uso), dado o custo fixo do agregador.
- **QA-02** — Categorização por LLM (FR-016): qual modelo, custo e se roda local ou via API.
- **QA-03** — Suporte a investimentos e crédito (demais escopos do Grupo DC) — fora do MVP.
