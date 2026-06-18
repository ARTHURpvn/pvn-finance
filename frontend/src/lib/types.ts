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
