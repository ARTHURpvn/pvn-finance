# ADR-002 — Port/Adapter com domínio espelhando o Open Finance

**Status:** Aceito · **Data:** 2026-06

## Contexto
O MVP usa Pluggy, mas o objetivo é virar SaaS e talvez, no futuro, integrar o Open Finance direto ou trocar de agregador. Pluggy/Belvo são, por baixo, wrappers dos mesmos endpoints do Open Finance (`/accounts → /balances → /transactions`, ciclo de `consents`).

## Decisão
Definir uma `FinancialDataPort` (interface) cujo formato **espelha o modelo canônico do Open Finance**. O domínio (Conexão, Conta, Transação, Categoria) depende só da Port. Cada provedor é um adapter (`PluggyAdapter` no MVP). A doc das APIs do Open Finance é a especificação de referência da Port.

## Consequências
- (+) Trocar de agregador ou plugar OF direto = novo adapter, núcleo intacto (NFR-006).
- (+) Testes de contrato isolam o domínio do fornecedor.
- (−) Custo inicial de modelar a camada de tradução provider → domínio.
