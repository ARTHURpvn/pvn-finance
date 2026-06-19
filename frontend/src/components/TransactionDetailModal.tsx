import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { display } from '@/lib/styles'
import { apiFetch } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useUi } from '@/lib/ui'
import type { Category, Transaction } from '@/lib/types'

export function TransactionDetailModal({
  tx,
  onClose,
  onUpdated,
}: {
  tx: Transaction
  onClose: () => void
  onUpdated: () => void
}) {
  const { money } = useUi()
  const [categories, setCategories] = useState<Category[]>([])
  const [categoryId, setCategoryId] = useState(tx.category_id ?? '')
  const [createRule, setCreateRule] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    apiFetch<Category[]>('/categories')
      .then(setCategories)
      .catch(() => undefined)
  }, [])

  async function save() {
    if (!categoryId) return
    setSaving(true)
    try {
      await apiFetch(`/transactions/${tx.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ category_id: categoryId, create_rule: createRule }),
      })
      toast.success('Transação reclassificada')
      onUpdated()
      onClose()
    } catch {
      toast.error('Falha ao reclassificar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 80,
        background: 'rgba(10,12,22,.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        animation: 'fadeIn .2s ease',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 440,
          maxWidth: '100%',
          background: 'var(--panel)',
          border: '1px solid var(--line)',
          borderRadius: 20,
          boxShadow: 'var(--shadow)',
          overflow: 'hidden',
          animation: 'pop .26s cubic-bezier(.2,.8,.3,1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--line)' }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>Detalhe da transação</span>
          <button onClick={onClose} style={{ cursor: 'pointer', border: 'none', background: 'transparent', color: 'var(--ink-soft)', fontSize: 18 }}>
            ✕
          </button>
        </div>
        <div style={{ padding: '22px 22px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <span style={{ width: 52, height: 52, borderRadius: 14, background: 'var(--fill)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24 }}>
              {tx.direction === 'in' ? '↓' : '↑'}
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{tx.description}</div>
              <div style={{ fontSize: 13, color: 'var(--ink-soft)' }}>
                {tx.category_name ?? 'Sem categoria'} · {formatDate(tx.date)}
              </div>
            </div>
            <div style={{ ...display, fontSize: 24, color: tx.direction === 'in' ? 'var(--ok)' : 'var(--ink)' }}>
              {money(tx.amount)}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--ink-soft)', fontWeight: 600 }}>Categoria</span>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              style={{
                border: '1.5px solid var(--line-2)',
                borderRadius: 11,
                padding: '11px 13px',
                fontSize: 14,
                background: 'var(--panel-2)',
                color: 'var(--ink)',
                fontFamily: 'var(--sans)',
              }}
            >
              <option value="">Selecione…</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--ink-soft)', marginTop: 2 }}>
              <input type="checkbox" checked={createRule} onChange={(e) => setCreateRule(e.target.checked)} />
              Criar regra para transações parecidas
            </label>
          </div>

          <button
            onClick={save}
            disabled={saving || !categoryId}
            style={{
              cursor: 'pointer',
              fontFamily: 'var(--sans)',
              fontWeight: 700,
              fontSize: 14,
              padding: 12,
              border: 'none',
              borderRadius: 11,
              background: 'var(--accent)',
              color: 'var(--accent-ink)',
              opacity: saving || !categoryId ? 0.6 : 1,
            }}
          >
            {saving ? 'Salvando…' : 'Reclassificar'}
          </button>
        </div>
      </div>
    </div>
  )
}
