import { useCallback, useEffect, useState } from 'react'
import { PluggyConnect } from 'react-pluggy-connect'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import {
  IconBolt,
  IconMoon,
  IconPlus,
  IconPower,
  IconRefresh,
  IconSun,
  IconTrash,
} from '@/components/icons'
import { display } from '@/lib/styles'
import { ApiError, apiFetch } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'
import { formatDate } from '@/lib/format'
import type {
  Connection,
  ConnectTokenResponse,
  PluggyCredentialStatus,
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
  const [pluggyOk, setPluggyOk] = useState(false)

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
    <div style={{ animation: 'fadeUp .32s ease', display: 'flex', flexDirection: 'column', gap: 18, width: '100%', maxWidth: 880 }}>
      <div style={{ ...display, fontSize: 26 }}>Configurações</div>

      <PluggyCredentialsCard onChange={setPluggyOk} />

      <Card style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 700, fontSize: 17 }}>Contas e bancos</span>
          <span style={{ fontFamily: 'var(--sans)', fontWeight: 700, fontSize: 11.5, padding: '5px 11px', borderRadius: 30, background: 'var(--accent2)', color: '#fff', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <IconBolt size={12} /> via Pluggy
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
            <button onClick={() => handleSync(c.id)} disabled={busy === c.id} className="u-ghost" style={ghostBtn}>
              <IconRefresh size={14} /> sincronizar
            </button>
            <button onClick={() => handleRemove(c.id)} disabled={busy === c.id} className="u-ghost" style={dangerBtn}>
              <IconTrash size={14} /> remover
            </button>
          </div>
        ))}

        <button onClick={handleConnect} disabled={!pluggyOk} className="u-ghost" title={pluggyOk ? '' : 'Configure suas credenciais Pluggy acima primeiro'} style={{ cursor: pluggyOk ? 'pointer' : 'not-allowed', opacity: pluggyOk ? 1 : 0.55, fontFamily: 'var(--sans)', fontWeight: 600, fontSize: 14, color: 'var(--accent)', background: 'transparent', border: '1.5px dashed var(--line-2)', borderRadius: 14, padding: 15, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          <IconPlus size={16} /> conectar nova conta via Pluggy
        </button>
        {!pluggyOk && (
          <div style={{ fontSize: 12, color: 'var(--ink-soft)', textAlign: 'center' }}>
            Configure suas credenciais Pluggy acima para poder conectar bancos.
          </div>
        )}
      </Card>

      <Card style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <span style={{ fontWeight: 700, fontSize: 16 }}>Aparência</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setTheme('light')} style={themeBtn(theme === 'light')}>
            <IconSun size={15} /> Claro
          </button>
          <button onClick={() => setTheme('dark')} style={themeBtn(theme === 'dark')}>
            <IconMoon size={15} /> Escuro
          </button>
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>
          Moeda: <b style={{ color: 'var(--ink)' }}>Real (R$)</b> · Idioma: Português
        </div>
      </Card>

      <button onClick={logout} className="u-ghost" style={{ alignSelf: 'flex-start', cursor: 'pointer', fontFamily: 'var(--sans)', fontWeight: 600, fontSize: 13.5, padding: '11px 18px', border: '1.5px solid var(--line-2)', borderRadius: 11, background: 'var(--panel)', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <IconPower size={16} /> Sair da conta
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

function PluggyCredentialsCard({ onChange }: { onChange: (ok: boolean) => void }) {
  const [status, setStatus] = useState<PluggyCredentialStatus | null>(null)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [baseUrl, setBaseUrl] = useState('https://api.pluggy.ai')
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)

  const load = useCallback(async () => {
    try {
      const s = await apiFetch<PluggyCredentialStatus>('/settings/pluggy')
      setStatus(s)
      onChange(s.configured)
      if (s.configured) {
        setClientId(s.client_id ?? '')
        setBaseUrl(s.base_url ?? 'https://api.pluggy.ai')
      }
    } catch {
      /* silencioso */
    }
  }, [onChange])

  useEffect(() => {
    void load()
  }, [load])

  async function save() {
    if (!clientId.trim() || !clientSecret.trim()) {
      toast.error('Preencha o Client ID e o Client Secret')
      return
    }
    setSaving(true)
    try {
      const s = await apiFetch<PluggyCredentialStatus>('/settings/pluggy', {
        method: 'PUT',
        body: JSON.stringify({
          client_id: clientId.trim(),
          client_secret: clientSecret,
          base_url: baseUrl.trim() || 'https://api.pluggy.ai',
        }),
      })
      setStatus(s)
      onChange(s.configured)
      setClientSecret('')
      setEditing(false)
      toast.success('Credenciais Pluggy salvas e validadas')
    } catch (e) {
      toast.error(
        e instanceof ApiError && e.status === 400
          ? 'Credenciais inválidas — o Pluggy recusou o Client ID/Secret'
          : 'Falha ao salvar as credenciais',
      )
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    if (!confirm('Remover suas credenciais Pluggy? Você não conseguirá sincronizar até cadastrar de novo.')) return
    try {
      await apiFetch('/settings/pluggy', { method: 'DELETE' })
      setStatus({ configured: false, client_id: null, base_url: null })
      setClientId('')
      setClientSecret('')
      onChange(false)
      toast.success('Credenciais removidas')
    } catch {
      toast.error('Falha ao remover')
    }
  }

  const configured = status?.configured ?? false
  const showForm = !configured || editing

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 700, fontSize: 17 }}>Credenciais Pluggy</span>
        <span
          style={{
            fontFamily: 'var(--sans)', fontWeight: 700, fontSize: 11.5, padding: '5px 11px', borderRadius: 30,
            background: configured ? 'var(--ok)' : 'var(--fill)',
            color: configured ? '#fff' : 'var(--ink-soft)',
          }}
        >
          {configured ? '● configurado' : 'não configurado'}
        </span>
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--ink-soft)', lineHeight: 1.5 }}>
        Pegue o <b style={{ color: 'var(--ink)' }}>Client ID</b> e o{' '}
        <b style={{ color: 'var(--ink)' }}>Client Secret</b> no dashboard do Pluggy
        (app.pluggy.ai → sua aplicação). Ficam cifrados e ligados à sua conta —
        o segredo nunca é exibido depois de salvo.
      </div>

      {configured && !editing ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200, fontSize: 13 }}>
            <div><span style={{ color: 'var(--ink-soft)' }}>Client ID:</span> {status?.client_id}</div>
            <div style={{ color: 'var(--ink-soft)' }}>Base URL: {status?.base_url}</div>
          </div>
          <button onClick={() => setEditing(true)} className="u-ghost" style={ghostBtn}>
            <IconRefresh size={14} /> atualizar
          </button>
          <button onClick={remove} className="u-ghost" style={dangerBtn}>
            <IconTrash size={14} /> remover
          </button>
        </div>
      ) : showForm ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input style={inputStyle} placeholder="Client ID" value={clientId} onChange={(e) => setClientId(e.target.value)} autoComplete="off" />
          <input style={inputStyle} type="password" placeholder="Client Secret" value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} autoComplete="new-password" />
          <input style={inputStyle} placeholder="Base URL (padrão https://api.pluggy.ai)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} autoComplete="off" />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={save} disabled={saving} style={{ ...primaryBtn, opacity: saving ? 0.6 : 1 }}>
              <IconBolt size={14} /> {saving ? 'validando…' : 'salvar e validar'}
            </button>
            {editing && (
              <button onClick={() => { setEditing(false); setClientSecret('') }} className="u-ghost" style={ghostBtn}>
                cancelar
              </button>
            )}
          </div>
        </div>
      ) : null}
    </Card>
  )
}

const inputStyle: React.CSSProperties = {
  fontFamily: 'var(--sans)',
  fontSize: 14,
  padding: '11px 13px',
  border: '1.5px solid var(--line-2)',
  borderRadius: 11,
  background: 'var(--panel)',
  color: 'var(--ink)',
  width: '100%',
  boxSizing: 'border-box',
}
const primaryBtn: React.CSSProperties = {
  cursor: 'pointer',
  fontFamily: 'var(--sans)',
  fontWeight: 700,
  fontSize: 13.5,
  padding: '10px 18px',
  border: 'none',
  borderRadius: 11,
  background: 'var(--accent)',
  color: 'var(--accent-ink)',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 7,
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
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
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
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  }
}
