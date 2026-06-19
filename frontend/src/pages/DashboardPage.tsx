import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import { IconArrowIn, IconArrowOut } from '@/components/icons'
import { display } from '@/lib/styles'
import { apiFetch } from '@/lib/api'
import { formatDate } from '@/lib/format'
import { useUi } from '@/lib/ui'
import type { AccountsResponse, DashboardSummary, TransactionsPage } from '@/lib/types'

interface CategorySpend {
  category: string
  total: string
}
interface TimelinePoint {
  month: string
  in: string
  out: string
}

const PALETTE = [
  'var(--accent)',
  'var(--accent2)',
  'var(--gold)',
  'var(--info)',
  'var(--ok)',
  'var(--danger)',
]

function donutGradient(values: number[]): string {
  const total = values.reduce((a, b) => a + b, 0) || 1
  let acc = 0
  const stops = values.map((v, i) => {
    const start = (acc / total) * 100
    acc += v
    const end = (acc / total) * 100
    return `${PALETTE[i % PALETTE.length]} ${start}% ${end}%`
  })
  return `conic-gradient(${stops.join(',')})`
}

function linePoints(values: number[], w = 460, h = 150, pad = 12): string {
  if (values.length === 0) return ''
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const span = max - min || 1
  const step = values.length > 1 ? w / (values.length - 1) : 0
  return values
    .map((v, i) => {
      const x = i * step
      const y = h - pad - ((v - min) / span) * (h - pad * 2)
      return `${x.toFixed(0)},${y.toFixed(0)}`
    })
    .join(' ')
}

export function DashboardPage() {
  const { money } = useUi()
  const [accounts, setAccounts] = useState<AccountsResponse | null>(null)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [byCategory, setByCategory] = useState<CategorySpend[]>([])
  const [timeline, setTimeline] = useState<TimelinePoint[]>([])
  const [recent, setRecent] = useState<TransactionsPage | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      apiFetch<AccountsResponse>('/accounts'),
      apiFetch<DashboardSummary>('/dashboard/summary'),
      apiFetch<CategorySpend[]>('/dashboard/by-category'),
      apiFetch<TimelinePoint[]>('/dashboard/timeline'),
      apiFetch<TransactionsPage>('/transactions?page=1&page_size=5'),
    ])
      .then(([a, s, c, t, r]) => {
        setAccounts(a)
        setSummary(s)
        setByCategory(c)
        setTimeline(t)
        setRecent(r)
      })
      .catch(() => toast.error('Falha ao carregar o painel'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ color: 'var(--ink-soft)' }}>Carregando…</p>

  const topCats = byCategory.slice(0, 5)
  const catTotal = byCategory.reduce((a, c) => a + Number(c.total), 0) || 1
  const donut = donutGradient(topCats.map((c) => Number(c.total)))
  const inflow = timeline.map((p) => Number(p.in) - Number(p.out))

  return (
    <div
      style={{
        animation: 'fadeUp .32s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: 18,
        maxWidth: 1180,
      }}
    >
      <div style={{ ...display, fontSize: 26 }}>Visão geral</div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Card dark style={{ flex: '1.5 1 280px' }}>
          <div style={{ fontSize: 13, color: 'var(--dark-soft)', fontWeight: 600 }}>
            Patrimônio total
          </div>
          <div style={{ ...display, fontSize: 40, lineHeight: 1.1 }}>
            {money(accounts?.summary.total ?? '0')}
          </div>
          <div style={{ fontSize: 13, color: 'var(--dark-soft)' }}>
            cartão de crédito à parte: {money(accounts?.summary.credit_card ?? '0')}
          </div>
        </Card>
        <Card style={{ flex: '1 1 160px' }}>
          <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>
            Entrou
          </div>
          <div style={{ ...display, fontSize: 30, color: 'var(--ok)' }}>
            + {money(summary?.received ?? '0')}
          </div>
        </Card>
        <Card style={{ flex: '1 1 160px' }}>
          <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>
            Saiu
          </div>
          <div style={{ ...display, fontSize: 30, color: 'var(--danger)' }}>
            − {money(summary?.spent ?? '0')}
          </div>
        </Card>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Card style={{ flex: '1.6 1 340px', display: 'flex', flexDirection: 'column', height: 248 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>Evolução (líquido mensal)</span>
            <span style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
              {timeline.length} {timeline.length === 1 ? 'mês' : 'meses'}
            </span>
          </div>
          {inflow.length > 0 ? (
            <svg viewBox="0 0 460 150" preserveAspectRatio="none" style={{ width: '100%', flex: 1, marginTop: 8 }}>
              <line x1="0" y1="130" x2="460" y2="130" stroke="var(--line)" strokeWidth="1" />
              <polyline
                fill="none"
                stroke="var(--accent)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={linePoints(inflow)}
              />
            </svg>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-soft)', fontSize: 13 }}>
              Sem dados ainda
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--ink-soft)' }}>
            {timeline.map((p) => (
              <span key={p.month}>{p.month.slice(5)}</span>
            ))}
          </div>
        </Card>

        <Card style={{ flex: '1 1 280px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Onde foi o dinheiro</span>
          {topCats.length > 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ position: 'relative', width: 104, height: 104, borderRadius: '50%', background: donut, flexShrink: 0 }}>
                <div style={{ position: 'absolute', inset: 22, background: 'var(--panel)', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: 10, color: 'var(--ink-soft)' }}>gasto</span>
                  <span style={{ ...display, fontSize: 14 }}>{money(summary?.spent ?? '0')}</span>
                </div>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 7 }}>
                {topCats.map((g, i) => (
                  <div key={g.category} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5 }}>
                    <span style={{ width: 9, height: 9, borderRadius: 3, background: PALETTE[i % PALETTE.length] }} />
                    <span style={{ flex: 1 }}>{g.category}</span>
                    <span style={{ color: 'var(--ink-soft)' }}>
                      {Math.round((Number(g.total) / catTotal) * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--ink-soft)', fontSize: 13 }}>Sem gastos no período.</div>
          )}
        </Card>
      </div>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Transações recentes</span>
          <Link to="/extrato" style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 600 }}>
            ver todas →
          </Link>
        </div>
        {recent && recent.items.length > 0 ? (
          recent.items.map((t) => (
            <div key={t.id} className="u-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '11px 8px', borderRadius: 10 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ width: 36, height: 36, borderRadius: 10, background: t.direction === 'in' ? 'color-mix(in srgb, var(--ok) 14%, transparent)' : 'var(--fill)', color: t.direction === 'in' ? 'var(--ok)' : 'var(--ink-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {t.direction === 'in' ? <IconArrowIn size={17} /> : <IconArrowOut size={17} />}
                </span>
                <span>
                  <span style={{ fontSize: 14, fontWeight: 600, display: 'block' }}>{t.description}</span>
                  <span style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
                    {formatDate(t.date)} · {t.category_name ?? 'Sem categoria'}
                  </span>
                </span>
              </span>
              <span style={{ ...display, fontWeight: 600, fontSize: 15, color: t.direction === 'in' ? 'var(--ok)' : 'var(--ink)' }}>
                {money(t.amount)}
              </span>
            </div>
          ))
        ) : (
          <div style={{ color: 'var(--ink-soft)', fontSize: 13, padding: '12px 8px' }}>
            Nenhuma transação. Conecte um banco em Configurações.
          </div>
        )}
      </Card>
    </div>
  )
}
