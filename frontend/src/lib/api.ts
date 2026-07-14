import type { ApiErrorBody } from './types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const TOKEN_KEY = 'consolida.access_token'
const REFRESH_KEY = 'consolida.refresh_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(TOKEN_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export class ApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.code = code
    this.status = status
  }
}

/** Evento disparado quando a sessão expira de vez (refresh falhou). O
 * AuthProvider escuta e redireciona para o login. */
export const AUTH_EXPIRED_EVENT = 'auth:expired'

// Um único refresh em voo por vez: o backend rotaciona o refresh token, então
// duas chamadas concorrentes com o mesmo token invalidariam a família. Todas as
// requisições que tomarem 401 ao mesmo tempo compartilham esta promise.
let refreshInFlight: Promise<boolean> | null = null

async function renewTokens(): Promise<boolean> {
  const refresh = tokenStore.getRefresh()
  if (!refresh) return false
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) return false
    const data = (await res.json()) as {
      access_token: string
      refresh_token: string
    }
    tokenStore.set(data.access_token, data.refresh_token)
    return true
  } catch {
    return false
  }
}

function refreshOnce(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = renewTokens().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const send = () => {
    const headers = new Headers(options.headers)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    const token = tokenStore.get()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return fetch(`${BASE_URL}${path}`, { ...options, headers })
  }

  let response = await send()

  // Access token expirado: tenta renovar (uma vez) e refaz a requisição.
  // Rotas /auth/* não passam pelo refresh (401 ali = credencial inválida).
  const isAuthRoute = path.startsWith('/auth/')
  if (response.status === 401 && !isAuthRoute && tokenStore.getRefresh()) {
    const renewed = await refreshOnce()
    if (renewed) {
      response = await send()
    } else {
      tokenStore.clear()
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
    }
  }

  if (response.status === 204) return undefined as T

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const body = data as ApiErrorBody | null
    throw new ApiError(
      body?.error?.message ?? 'Erro inesperado',
      body?.error?.code ?? 'unknown',
      response.status,
    )
  }

  return data as T
}
