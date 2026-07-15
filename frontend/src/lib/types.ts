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

export interface Investment {
  name: string
  type: string
  balance: string
  is_reserve: boolean
}

export interface AccountsResponse {
  accounts: Account[]
  investments: Investment[]
  summary: {
    total: string
    cash: string
    reserves: string
    investments: string
    credit_card: string
  }
}

export interface Transaction {
  id: string
  account_id: string
  account_type: string | null
  account_name: string | null
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

export interface Category {
  id: string
  name: string
  kind: 'income' | 'expense' | 'transfer'
  is_system: boolean
  parent_id: string | null
}

export interface DashboardSummary {
  received: string
  spent: string
  net: string
}

export interface Subscription {
  name: string
  slug: string
  color: string
  monthly_amount: string
  occurrences: number
  months: number
  last_date: string
  category: string | null
}

export interface SubscriptionsResponse {
  subscriptions: Subscription[]
  monthly_total: string
}

export interface InvestmentDetail {
  name: string
  type: string
  subtype: string | null
  bank: string | null
  balance: string
  amount_original: string | null
  profit: string | null
  is_fixed_income: boolean
  rate: string | null
  rate_type: string | null
  annual_rate: string | null
  monthly_income: string
  due_date: string | null
  purchase_date: string | null
}

export interface InvestmentEvolutionPoint {
  month: string
  total: string
}

export interface InvestmentsSummary {
  total_invested: string
  total_profit: string
  monthly_income: string
  cdi_annual_rate: string
}

export interface InvestmentsResponse {
  investments: InvestmentDetail[]
  summary: InvestmentsSummary
  evolution: InvestmentEvolutionPoint[]
}
