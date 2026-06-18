# DATA_MODEL — Consolida

Modelo espelha o canônico do Open Finance. **Tudo é escopado por `user_id`** (multi-tenant-ready).

## Diagrama ER

```mermaid
erDiagram
    USERS ||--o{ CONNECTIONS : tem
    USERS ||--o{ CATEGORIES : define
    USERS ||--o{ RULES : define
    CONNECTIONS ||--o{ ACCOUNTS : agrega
    CONNECTIONS ||--o{ SYNC_LOGS : registra
    ACCOUNTS ||--o{ TRANSACTIONS : contém
    CATEGORIES ||--o{ TRANSACTIONS : classifica
    CATEGORIES ||--o{ RULES : alvo
    CATEGORIES ||--o{ CATEGORIES : pai

    USERS {
        uuid id PK
        string email UK
        string password_hash
        timestamp created_at
    }
    CONNECTIONS {
        uuid id PK
        uuid user_id FK
        string provider
        string provider_item_id
        string institution_name
        string status
        bytea encrypted_secret
        timestamp consent_expires_at
        timestamp last_sync_at
    }
    ACCOUNTS {
        uuid id PK
        uuid user_id FK
        uuid connection_id FK
        string provider_account_id
        string type
        string name
        string currency
        numeric balance
        timestamp balance_updated_at
    }
    TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        uuid account_id FK
        string provider_transaction_id
        date date
        numeric amount
        string direction
        string description
        string counterpart
        uuid category_id FK
        jsonb raw
    }
    CATEGORIES {
        uuid id PK
        uuid user_id FK
        uuid parent_id FK
        string name
        string kind
        bool is_system
    }
    RULES {
        uuid id PK
        uuid user_id FK
        string match_type
        string pattern
        uuid category_id FK
        int priority
    }
    SYNC_LOGS {
        uuid id PK
        uuid connection_id FK
        timestamp started_at
        timestamp finished_at
        string status
        string error
    }
```

## Dicionário de dados (campos não-óbvios)

| Tabela.campo | Notas |
|---|---|
| `connections.provider` | Identifica o adapter (`pluggy`, futuro `openfinance`, `belvo`). |
| `connections.provider_item_id` | ID do vínculo no agregador (no Pluggy: *Item*). |
| `connections.status` | `ativa` · `requer_reauth` · `erro` (RN-03). |
| `connections.encrypted_secret` | Token/credencial do agregador cifrado em repouso (NFR-001). Nunca exposto via API. |
| `connections.consent_expires_at` | Validade do consentimento (≤ 12 meses). |
| `accounts.type` | `checking` · `savings` · `payment` · `credit_card`. Cartão entra como passivo (RN-02). |
| `transactions.direction` | `in` (crédito) · `out` (débito). Derivado do sinal do `amount` (RN-01). |
| `transactions.provider_transaction_id` | Parte da chave de dedupe `(connection_id, provider_transaction_id)` (RN-05). |
| `transactions.raw` | Payload original do agregador (auditoria/reprocesso). Sem expor cru na API. |
| `transactions` | Imutável após import; só `category_id` muda na recategorização (RN-04). |
| `categories.is_system` | Categorias padrão do sistema (`user_id` nulo) vs. do usuário. |
| `categories.kind` | `income` · `expense` · `transfer`. |
| `rules.match_type` | `contains` · `equals` · `regex`. Aplicadas por `priority`. |

## Índices essenciais (NFR-005 / NFR-007)

- `transactions (user_id, date)`, `transactions (account_id, date)`
- `UNIQUE (connection_id, provider_transaction_id)`
- `accounts (user_id)`, `connections (user_id)`
