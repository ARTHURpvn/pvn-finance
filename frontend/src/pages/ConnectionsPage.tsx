import { useCallback, useEffect, useState } from 'react'
import { PluggyConnect } from 'react-pluggy-connect'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import type {
  Connection,
  ConnectTokenResponse,
  SyncResult,
} from '@/lib/types'

interface PluggyItemData {
  item: { id: string; connector?: { name?: string } }
}

type ConnectFlow = {
  token: string
  onComplete: (data: PluggyItemData) => Promise<void>
}

const STATUS_LABEL: Record<Connection['status'], string> = {
  ativa: 'Ativa',
  requer_reauth: 'Requer reautenticação',
  erro: 'Erro',
}

function statusVariant(
  status: Connection['status'],
): 'default' | 'secondary' | 'destructive' {
  if (status === 'ativa') return 'default'
  if (status === 'erro') return 'destructive'
  return 'secondary'
}

export function ConnectionsPage() {
  const { user, logout } = useAuth()
  const [connections, setConnections] = useState<Connection[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [connect, setConnect] = useState<ConnectFlow | null>(null)

  const load = useCallback(async () => {
    try {
      setConnections(await apiFetch<Connection[]>('/connections'))
    } catch {
      toast.error('Falha ao carregar conexões')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleConnectNew() {
    try {
      const { connect_token } = await apiFetch<ConnectTokenResponse>(
        '/connections',
        { method: 'POST' },
      )
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
          const result = await apiFetch<SyncResult>(
            `/connections/${conn.id}/sync`,
            { method: 'POST' },
          )
          toast.success(
            `Banco conectado — ${result.imported} transações importadas`,
          )
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
      const result = await apiFetch<SyncResult>(`/connections/${id}/sync`, {
        method: 'POST',
      })
      toast.success(`Sincronizado — ${result.imported} novas transações`)
      await load()
    } catch {
      toast.error('Falha ao sincronizar')
    } finally {
      setBusy(null)
    }
  }

  async function handleReauth(id: string) {
    try {
      const { connect_token } = await apiFetch<ConnectTokenResponse>(
        `/connections/${id}/reauth`,
        { method: 'POST' },
      )
      setConnect({
        token: connect_token,
        onComplete: async () => {
          toast.success('Conexão reautenticada')
          await load()
        },
      })
    } catch {
      toast.error('Não foi possível reautenticar')
    }
  }

  async function handleDelete(id: string) {
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
    <div className="min-h-svh">
      <header className="border-b">
        <div className="max-w-3xl mx-auto flex items-center justify-between p-4">
          <h1 className="text-lg font-semibold">Consolida</h1>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-muted-foreground">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Conexões bancárias</h2>
            <p className="text-sm text-muted-foreground">
              Conecte seus bancos para consolidar transações.
            </p>
          </div>
          <Button onClick={handleConnectNew}>Conectar banco</Button>
        </div>

        {loading ? (
          <p className="text-muted-foreground">Carregando…</p>
        ) : connections.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-muted-foreground">
              Nenhuma conexão ainda. Clique em “Conectar banco”.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3">
            {connections.map((conn) => (
              <Card key={conn.id}>
                <CardHeader className="flex flex-row items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">
                      {conn.institution_name}
                    </CardTitle>
                    <CardDescription>
                      {conn.last_sync_at
                        ? `Última sync: ${new Date(conn.last_sync_at).toLocaleString('pt-BR')}`
                        : 'Nunca sincronizado'}
                    </CardDescription>
                  </div>
                  <Badge variant={statusVariant(conn.status)}>
                    {STATUS_LABEL[conn.status]}
                  </Badge>
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleSync(conn.id)}
                    disabled={busy === conn.id}
                  >
                    Sincronizar
                  </Button>
                  {conn.status === 'requer_reauth' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReauth(conn.id)}
                    >
                      Reautenticar
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-destructive"
                    onClick={() => handleDelete(conn.id)}
                    disabled={busy === conn.id}
                  >
                    Remover
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

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
