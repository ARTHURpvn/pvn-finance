export interface ApiErrorBody {
  error: { code: string; message: string }
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  created_at: string
}

export interface Connection {
  id: string
  provider: string
  institution_name: string
  status: 'ativa' | 'requer_reauth' | 'erro'
  consent_expires_at: string | null
  last_sync_at: string | null
}

export interface ConnectTokenResponse {
  connect_token: string
}

export interface SyncResult {
  status: string
  imported: number
}

export interface Account {
  id: string
  connection_id: string
  type: 'checking' | 'savings' | 'payment' | 'credit_card'
  name: string
  currency: string
  balance: string
  balance_updated_at: string | null
}

export interface AccountsResponse {
  accounts: Account[]
  summary: { total: string; credit_card: string }
}

export interface Transaction {
  id: string
  account_id: string
  date: string
  amount: string
  direction: 'in' | 'out'
  description: string
  counterpart: string | null
  category_id: string | null
  category_name: string | null
}

export interface TransactionsPage {
  items: Transaction[]
  page: number
  page_size: number
  total: number
}
