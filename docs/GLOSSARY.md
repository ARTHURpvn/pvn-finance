# GLOSSARY — Consolida

| Termo | Definição no contexto do projeto |
|---|---|
| **Open Finance Brasil** | Ecossistema regulado pelo BCB para compartilhamento padronizado de dados/serviços financeiros mediante consentimento. |
| **Agregador / TPP** | Empresa que já é participante certificada e expõe API amigável sobre o Open Finance. No MVP: **Pluggy**. |
| **Receptor de dados** | Papel (Fase 2) de quem consome dados do cliente; exige certificação FAPI/DCR e registro no Diretório. |
| **Instituição transmissora** | Banco detentor dos dados/contas do cliente, que os envia mediante consentimento. |
| **Diretório de Participantes** | Repositório onde uma instituição autorizada pelo BC formaliza participação e obtém o SSA. |
| **SSA** | *Software Statement Assertion* — credencial emitida pelo Diretório, obrigatória para o DCR. |
| **DCR** | *Dynamic Client Registration* — registro dinâmico do cliente no Authorization Server do banco. |
| **FAPI** | *Financial-grade API* — perfil de segurança OAuth/OIDC do setor financeiro. |
| **mTLS** | TLS mútuo; comunicação com certificados bilaterais (BRCAC transporte / BRSEAL assinatura). |
| **Consentimento** | Autorização explícita e temporária do cliente (dados: até 12 meses) para compartilhar dados com um receptor. |
| **Conexão (Item)** | Nossa entidade que representa o vínculo de um banco do usuário via agregador (no Pluggy: *Item*). |
| **Conta** | Conta agregada (corrente, poupança, pagamento, cartão) trazida por uma Conexão. |
| **Transação** | Lançamento de uma conta (entrada/saída) com data, valor, sinal, descrição e categoria. |
| **Categoria** | Classificação de uma transação (do agregador, de regra do usuário ou manual). |
| **Regra** | Critério do usuário (ex.: "descrição contém X") que define a categoria de transações correspondentes. |
| **Port / Adapter** | Padrão hexagonal: *Port* é a interface que o domínio espera; *Adapter* (Pluggy) a implementa. |
| **Multi-tenant** | Vários clientes isolados na mesma aplicação; aqui o schema já isola por `user_id` desde o MVP. |
| **Defasagem (tempestividade)** | Atraso aceitável dos dados (ex.: minutos para saldo, mais para crédito/investimento). |
