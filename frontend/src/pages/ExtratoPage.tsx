import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import { TransactionDetailModal } from '@/components/TransactionDetailModal'
import { TransactionRow } from '@/components/TransactionRow'
import { IconSearch } from '@/components/icons'
import { apiFetch } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { display } from '@/lib/styles'
import { useUi } from '@/lib/ui'
import type { Transaction, TransactionsPage } from '@/lib/types'

const PAGE_SIZE = 50

export function ExtratoPage() {
  const { money } = useUi()
  const [data, setData] = useState<TransactionsPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Transaction | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
      exclude_transfers: 'true', // esconde movimentação interna (Rende Fácil,
      // transferência entre contas próprias, pagamento de fatura)
    })
    if (q) params.set('q', q)
    try {
      setData(await apiFetch<TransactionsPage>(`/transactions?${params}`))
    } catch {
      toast.error('Falha ao carregar transações')
    } finally {
      setLoading(false)
    }
  }, [page, q])

  useEffect(() => {
    void load()
  }, [load])

  const groups = useMemo(() => {
    const map = new Map<string, Transaction[]>()
    for (const t of data?.items ?? []) {
      const arr = map.get(t.date) ?? []
      arr.push(t)
      map.set(t.date, arr)
    }
    return [...map.entries()].sort((a, b) => (a[0] < b[0] ? 1 : -1))
  }, [data])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <div style={{ animation: 'fadeUp .32s ease', display: 'flex', flexDirection: 'column', gap: 16, width: '100%', maxWidth: 1040 }}>
      <div style={{ ...display, fontSize: 26 }}>Extrato</div>

      <div style={{ position: 'relative' }}>
        <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--ink-soft)', display: 'flex' }}>
          <IconSearch size={17} />
        </span>
        <input
          value={q}
          onChange={(e) => {
            setPage(1)
            setQ(e.target.value)
          }}
          placeholder="Buscar transação…"
          className="u-field"
          style={{
            width: '100%',
            border: '1.5px solid var(--line-2)',
            borderRadius: 12,
            padding: '12px 15px 12px 40px',
            fontSize: 14,
            color: 'var(--ink)',
            background: 'var(--panel)',
            fontFamily: 'var(--sans)',
            outline: 'none',
          }}
        />
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <div className="u-spinner" />
        </div>
      ) : groups.length === 0 ? (
        <Card style={{ textAlign: 'center', color: 'var(--ink-soft)', padding: '40px 20px' }}>
          Nenhuma transação encontrada.
        </Card>
      ) : (
        groups.map(([day, items]) => {
          const dayTotal = items.reduce((a, t) => a + Number(t.amount), 0)
          return (
            <Card key={day} style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '13px 18px', borderBottom: '1px solid var(--line)', background: 'var(--panel-2)' }}>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{formatDate(day)}</span>
                <span style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>
                  total do dia{' '}
                  <b style={{ ...display, color: dayTotal >= 0 ? 'var(--ok)' : 'var(--danger)' }}>
                    {money(dayTotal)}
                  </b>
                </span>
              </div>
              {items.map((t, idx) => (
                <TransactionRow
                  key={t.id}
                  tx={t}
                  onClick={() => setSelected(t)}
                  borderTop={idx > 0}
                />
              ))}
            </Card>
          )
        })
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 13, color: 'var(--ink-soft)' }}>{data?.total ?? 0} transações</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="u-ghost" style={pagBtn(page <= 1)}>
            Anterior
          </button>
          <span style={{ fontSize: 13 }}>
            {page} / {totalPages}
          </span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="u-ghost" style={pagBtn(page >= totalPages)}>
            Próxima
          </button>
        </div>
      </div>

      {selected && (
        <TransactionDetailModal
          tx={selected}
          onClose={() => setSelected(null)}
          onUpdated={load}
        />
      )}
    </div>
  )
}

function pagBtn(disabled: boolean): React.CSSProperties {
  return {
    cursor: disabled ? 'default' : 'pointer',
    fontFamily: 'var(--sans)',
    fontWeight: 600,
    fontSize: 13,
    padding: '7px 14px',
    border: '1.5px solid var(--line-2)',
    borderRadius: 10,
    background: 'var(--panel)',
    color: 'var(--ink)',
    opacity: disabled ? 0.5 : 1,
  }
}
