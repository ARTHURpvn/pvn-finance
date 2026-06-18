# Consolida

> Nome de trabalho provisório. Agregador financeiro pessoal (leitura) via Open Finance, por meio de agregador certificado, desenhado para virar SaaS.

## Visão em uma frase
Conectar todas as contas bancárias do usuário e responder, sem planilha, **quanto entrou, quanto saiu e pra onde foi** — por período e por categoria.

## Stack
- **Backend:** Python · FastAPI · SQLAlchemy · Alembic
- **Frontend:** Vite · React · TypeScript · shadcn/ui
- **Banco:** PostgreSQL (Docker)
- **Dados bancários:** agregador certificado (**Pluggy** no MVP) atrás de uma camada **Port/Adapter**
- **Padrão:** hexagonal; domínio espelha o modelo canônico do Open Finance

## Decisão central
Não dá pra usar a API do Open Finance direto sem ser instituição autorizada pelo BC. O MVP usa Pluggy como adapter; a Port deixa trocar de agregador (ou plugar OF direto) sem reescrever o núcleo. Detalhe em `adr/ADR-001` e `adr/ADR-002`.

## Mapa de documentos
| Arquivo | O que é |
|---|---|
| `VISION.md` | Visão, escopo, stakeholders |
| `SRS.md` | Requisitos funcionais e não-funcionais, regras, restrições, premissas |
| `USE_CASES.md` | Casos de uso (diagrama + Gherkin) |
| `GLOSSARY.md` | Termos do domínio |
| `ARCHITECTURE.md` | Componentes, fluxo de sync, decisões |
| `DATA_MODEL.md` | Diagrama ER + dicionário de dados |
| `API.md` | Contrato da API interna |
| `adr/ADR-001..005` | Decisões técnicas registradas |
| `TEST_STRATEGY.md` | Estratégia de testes |
| `TRACEABILITY.md` | Matriz requisito → feature → teste |
| `RISKS.md` | Matriz de riscos |
| `ROADMAP.md` | Features na ordem de construção, prontas pra `/feature` |
| `SRS.docx` · `Visao.docx` | Versões para compartilhar |
| `requisitos.xlsx` | Rastreabilidade + Riscos (manipulável) |

## Convenções
- IDs: requisitos `FR-/NFR-`, regras `RN-`, riscos `R-`, decisões `ADR-`. O roadmap e a rastreabilidade referenciam esses IDs.
- Defaults de stack e padrões de código no `CLAUDE.md` do projeto (a criar na F1).

## Próximo passo
Rodar `ROADMAP.md` em ordem (F1 → F10) com `/feature`. Começar por **F1 — Bootstrap & infra**.
