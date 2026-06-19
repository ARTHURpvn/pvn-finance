import { useCallback, useEffect, useState } from 'react'
import { PluggyConnect } from 'react-pluggy-connect'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import { display } from '@/lib/styles'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'
import { formatDate } from '@/lib/format'
import type {
  Connection,
  ConnectTokenResponse,
  SyncResult,
} from '@/lib/types'

interface PluggyItemData {
  item: { id: string; connector?: { name?: string } }
}
type ConnectFlow = { token: string; onComplete: (d: PluggyItemData) => Promise<void> }

const STATUS_LABEL: Record<Connection['status'], string> = {
  ativa: 'sincronizado',
  requer_reauth: 'requer reautenticação',
  erro: 'erro',
}

export function ConfigPage() {
  const { logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const [connections, setConnections] = useState<Connection[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [connect, setConnect] = useState<ConnectFlow | null>(null)

  const load = useCallback(async () => {
    try {
      setConnections(await apiFetch<Connection[]>('/connections'))
    } catch {
      toast.error('Falha ao carregar conexões')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleConnect() {
    try {
      const { connect_token } = await apiFetch<ConnectTokenResponse>('/connections', { method: 'POST' })
      setConnect({
        token: connect_token,
        onComplete: async (data) => {
          const conn = await apiFetch<Connection>('/connections/register', {
            method: 'POST',
            body: JSON.stringify({
              provider_item_id: data.item.id,
              institution_name: data.item.connector?.name ?? 'Banco',
            }),
          })
          const result = await apiFetch<SyncResult>(`/connections/${conn.id}/sync`, { method: 'POST' })
          toast.success(`Banco conectado — ${result.imported} transações`)
          await load()
        },
      })
    } catch {
      toast.error('Não foi possível iniciar a conexão')
    }
  }

  async function handleSync(id: string) {
    setBusy(id)
    try {
      const r = await apiFetch<SyncResult>(`/connections/${id}/sync`, { method: 'POST' })
      toast.success(`Sincronizado — ${r.imported} novas`)
      await load()
    } catch {
      toast.error('Falha ao sincronizar')
    } finally {
      setBusy(null)
    }
  }

  async function handleRemove(id: string) {
    if (!confirm('Remover esta conexão e todos os dados associados?')) return
    setBusy(id)
    try {
      await apiFetch(`/connections/${id}`, { method: 'DELETE' })
      toast.success('Conexão removida')
      await load()
    } catch {
      toast.error('Falha ao remover')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div style={{ animation: 'fadeUp .32s ease', display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 880 }}>
      <div style={{ ...display, fontSize: 26 }}>Configurações</div>

      <Card style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 700, fontSize: 17 }}>Contas e bancos</span>
          <span style={{ fontFamily: 'var(--sans)', fontWeight: 700, fontSize: 11.5, padding: '5px 11px', borderRadius: 30, background: 'var(--accent2)', color: '#fff' }}>
            ⚡ via Pluggy
          </span>
        </div>

        {connections.length === 0 && (
          <div style={{ color: 'var(--ink-soft)', fontSize: 13.5 }}>
            Nenhuma conta conectada ainda.
          </div>
        )}

        {connections.map((c) => (
          <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 14, border: '1px solid var(--line)', borderRadius: 14, padding: '13px 16px' }}>
            <span style={{ width: 42, height: 42, borderRadius: 11, background: 'var(--fill)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 15 }}>
              {c.institution_name.slice(0, 2).toUpperCase()}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 600 }}>{c.institution_name}</div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
                <span style={{ color: c.status === 'ativa' ? 'var(--ok)' : c.status === 'erro' ? 'var(--danger)' : 'var(--gold)' }}>
                  ●
                </span>{' '}
                {STATUS_LABEL[c.status]}
                {c.last_sync_at ? ` · ${formatDate(c.last_sync_at)}` : ''}
              </div>
            </div>
            <button onClick={() => handleSync(c.id)} disabled={busy === c.id} style={ghostBtn}>
              sincronizar
            </button>
            <button onClick={() => handleRemove(c.id)} disabled={busy === c.id} style={dangerBtn}>
              remover
            </button>
          </div>
        ))}

        <button onClick={handleConnect} style={{ cursor: 'pointer', fontFamily: 'var(--sans)', fontWeight: 600, fontSize: 14, color: 'var(--accent)', background: 'transparent', border: '1.5px dashed var(--line-2)', borderRadius: 14, padding: 15 }}>
          + conectar nova conta via Pluggy
        </button>
      </Card>

      <Card style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 16 }}>Aparência</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setTheme('light')} style={themeBtn(theme === 'light')}>
            ☀ Claro
          </button>
          <button onClick={() => setTheme('dark')} style={themeBtn(theme === 'dark')}>
            ☾ Escuro
          </button>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>
          Moeda: <b style={{ color: 'var(--ink)' }}>Real (R$)</b> · Idioma: Português
        </div>
      </Card>

      <button onClick={logout} style={{ alignSelf: 'flex-start', cursor: 'pointer', fontFamily: 'var(--sans)', fontWeight: 600, fontSize: 13.5, padding: '11px 18px', border: '1.5px solid var(--line-2)', borderRadius: 11, background: 'var(--panel)', color: 'var(--danger)' }}>
        ⏻ Sair da conta
      </button>

      {connect && (
        <PluggyConnect
          connectToken={connect.token}
          includeSandbox
          onSuccess={async (data: PluggyItemData) => {
            const handler = connect.onComplete
            setConnect(null)
            try {
              await handler(data)
            } catch {
              toast.error('Falha ao registrar a conexão')
            }
          }}
          onError={() => {
            toast.error('Erro no Pluggy Connect')
            setConnect(null)
          }}
          onClose={() => setConnect(null)}
        />
      )}
    </div>
  )
}

const ghostBtn: React.CSSProperties = {
  cursor: 'pointer',
  fontFamily: 'var(--sans)',
  fontWeight: 600,
  fontSize: 12.5,
  padding: '7px 12px',
  border: '1.5px solid var(--line-2)',
  borderRadius: 9,
  background: 'transparent',
  color: 'var(--ink)',
}
const dangerBtn: React.CSSProperties = {
  ...ghostBtn,
  border: '1.5px solid var(--danger)',
  color: 'var(--danger)',
}
function themeBtn(active: boolean): React.CSSProperties {
  return {
    cursor: 'pointer',
    flex: 1,
    fontFamily: 'var(--sans)',
    fontWeight: 600,
    fontSize: 13,
    padding: 11,
    border: '1.5px solid var(--line-2)',
    borderRadius: 11,
    background: active ? 'var(--accent)' : 'var(--panel)',
    color: active ? 'var(--accent-ink)' : 'var(--ink)',
  }
}
