# ADR-001 — Acesso a dados via agregador, não Open Finance direto

**Status:** Aceito · **Data:** 2026-06

## Contexto
O acesso direto às APIs reguladas do Open Finance (Grupo DC: contas, saldos, transações) exige ser instituição autorizada pelo BCB, com certificação FAPI/DCR e registro no Diretório de Participantes para obter o SSA. A própria documentação do Open Finance afirma que apenas instituições autorizadas participam e que uma empresa de tecnologia precisa "operar em parceria com instituição participante ou obter autorização própria". Um produto indie não transpõe essa barreira sozinho.

## Decisão
Consumir os dados por meio de um **agregador certificado** (Pluggy no MVP), que atua como instituição participante e expõe API amigável. O Grupo DA (Dados Abertos) é público mas não traz dados pessoais, então não atende ao caso de uso.

## Consequências
- (+) Time-to-market: dá pra prototipar no trial e ter dados reais sem certificação.
- (−) Custo fixo mensal do agregador (ver RISKS R-01) e dependência de fornecedor (mitigada pelo ADR-002).
- (~) Caminho de "autorização própria" fica como opção futura, sem reescrever o núcleo (Port/Adapter).
