import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { apiFetch } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { Account, TransactionsPage as TxPage } from '@/lib/types'

const PAGE_SIZE = 20

export function TransactionsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [data, setData] = useState<TxPage | null>(null)
  const [loading, setLoading] = useState(true)

  // filtros aplicados
  const [q, setQ] = useState('')
  const [accountId, setAccountId] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    apiFetch<{ accounts: Account[] }>('/accounts')
      .then((r) => setAccounts(r.accounts))
      .catch(() => undefined)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    })
    if (q) params.set('q', q)
    if (accountId) params.set('account_id', accountId)
    if (from) params.set('from', from)
    if (to) params.set('to', to)
    try {
      setData(await apiFetch<TxPage>(`/transactions?${params.toString()}`))
    } catch {
      toast.error('Falha ao carregar transações')
    } finally {
      setLoading(false)
    }
  }, [page, q, accountId, from, to])

  useEffect(() => {
    void load()
  }, [load])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Extrato</h2>

      <Card>
        <CardContent className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-6">
          <div className="grid gap-1.5 sm:col-span-2">
            <Label htmlFor="q">Buscar</Label>
            <Input
              id="q"
              placeholder="Descrição…"
              value={q}
              onChange={(e) => {
                setPage(1)
                setQ(e.target.value)
              }}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="account">Conta</Label>
            <select
              id="account"
              className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
              value={accountId}
              onChange={(e) => {
                setPage(1)
                setAccountId(e.target.value)
              }}
            >
              <option value="">Todas</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="grid gap-1.5">
              <Label htmlFor="from">De</Label>
              <Input
                id="from"
                type="date"
                value={from}
                onChange={(e) => {
                  setPage(1)
                  setFrom(e.target.value)
                }}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="to">Até</Label>
              <Input
                id="to"
                type="date"
                value={to}
                onChange={(e) => {
                  setPage(1)
                  setTo(e.target.value)
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-muted-foreground">Carregando…</p>
      ) : !data || data.items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            Nenhuma transação encontrada.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="border-b text-muted-foreground">
                <tr>
                  <th className="text-left font-medium p-3">Data</th>
                  <th className="text-left font-medium p-3">Descrição</th>
                  <th className="text-left font-medium p-3 hidden sm:table-cell">
                    Categoria
                  </th>
                  <th className="text-right font-medium p-3">Valor</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((tx) => (
                  <tr key={tx.id} className="border-b last:border-0">
                    <td className="p-3 whitespace-nowrap text-muted-foreground">
                      {formatDate(tx.date)}
                    </td>
                    <td className="p-3">{tx.description}</td>
                    <td className="p-3 hidden sm:table-cell text-muted-foreground">
                      {tx.category_name ?? '—'}
                    </td>
                    <td
                      className={cn(
                        'p-3 text-right whitespace-nowrap font-medium',
                        tx.direction === 'in'
                          ? 'text-green-600'
                          : 'text-foreground',
                      )}
                    >
                      {formatCurrency(tx.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          {data?.total ?? 0} transações
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </Button>
          <span className="text-sm">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Próxima
          </Button>
        </div>
      </div>
    </div>
  )
}
