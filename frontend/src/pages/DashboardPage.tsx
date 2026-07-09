import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import { TransactionRow } from '@/components/TransactionRow'
import { IconArrowIn, IconArrowOut } from '@/components/icons'
import { display } from '@/lib/styles'
import { apiFetch } from '@/lib/api'
import { bankOf } from '@/lib/banks'
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

const MESES = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
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

function areaPoints(values: number[]): string {
  const pts = linePoints(values)
  if (!pts) return ''
  return `0,150 ${pts} 460,150`
}

function chip(color: string): React.CSSProperties {
  return {
    width: 34,
    height: 34,
    borderRadius: 10,
    background: `color-mix(in srgb, ${color} 16%, transparent)`,
    color,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
  }
}

export function DashboardPage() {
  const { money } = useUi()
  const [accounts, setAccounts] = useState<AccountsResponse | null>(null)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [byCategory, setByCategory] = useState<CategorySpend[]>([])
  const [timeline, setTimeline] = useState<TimelinePoint[]>([])
  const [recent, setRecent] = useState<TransactionsPage | null>(null)
  const [netByAccount, setNetByAccount] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Entrou/Saiu consideram apenas o mês corrente (não o histórico todo).
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const monthStart = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    const monthEnd = `${lastDay.getFullYear()}-${pad(lastDay.getMonth() + 1)}-${pad(lastDay.getDate())}`

    Promise.all([
      apiFetch<AccountsResponse>('/accounts'),
      apiFetch<DashboardSummary>(
        `/dashboard/summary?from=${monthStart}&to=${monthEnd}`,
      ),
      apiFetch<CategorySpend[]>(
        `/dashboard/by-category?from=${monthStart}&to=${monthEnd}`,
      ),
      apiFetch<TimelinePoint[]>('/dashboard/timeline'),
      apiFetch<TransactionsPage>(
        '/transactions?page=1&page_size=6&exclude_transfers=true',
      ),
      apiFetch<{ account_id: string; net: string }[]>(
        `/dashboard/by-account?from=${monthStart}&to=${monthEnd}`,
      ),
    ])
      .then(([a, s, c, t, r, n]) => {
        setAccounts(a)
        setSummary(s)
        setByCategory(c)
        setTimeline(t)
        setRecent(r)
        setNetByAccount(Object.fromEntries(n.map((x) => [x.account_id, x.net])))
      })
      .catch(() => toast.error('Falha ao carregar o painel'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ color: 'var(--ink-soft)' }}>Carregando…</p>

  const monthLabel = MESES[new Date().getMonth()]
  // Saldo por banco (híbrido): usa o saldo real do banco = conta corrente +
  // reservas de liquidez (Rende Fácil) daquele banco. Quando esse saldo vem
  // zerado (sandbox zera os balances), cai no líquido do mês (Entrou − Saiu)
  // como aproximação. Com o banco real conectado o saldo real prevalece.
  const banks = (() => {
    const map = new Map<
      string,
      { label: string; logo: string; balance: number; net: number }
    >()
    const bucket = (key: string, label: string, logo: string) => {
      const cur = map.get(key) ?? { label, logo, balance: 0, net: 0 }
      map.set(key, cur)
      return cur
    }
    for (const a of accounts?.accounts ?? []) {
      if (a.type === 'credit_card') continue
      const bank = bankOf(a.name)
      if (!bank) continue
      const cur = bucket(bank.key, bank.label, bank.logo)
      cur.balance += Number(a.balance ?? '0')
      cur.net += Number(netByAccount[a.id] ?? '0')
    }
    for (const inv of accounts?.investments ?? []) {
      if (!inv.is_reserve) continue
      const bank = bankOf(inv.name)
      if (!bank) continue
      bucket(bank.key, bank.label, bank.logo).balance += Number(inv.balance ?? '0')
    }
    return [...map.values()]
      .map((b) => ({
        label: b.label,
        logo: b.logo,
        total: b.balance !== 0 ? b.balance : b.net,
      }))
      .sort((a, b) => b.total - a.total)
  })()
  // Patrimônio total = soma dos saldos por banco (mantém total e bancos
  // coerentes). Investimentos de prazo ficam à parte (fora do saldo).
  const patrimonioTotal = banks.reduce((a, b) => a + b.total, 0)
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
        width: '100%',
        maxWidth: 1180,
      }}
    >
      <div style={{ ...display, fontSize: 26 }}>Visão geral</div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div
          className="u-card-hover"
          style={{
            flex: '1.5 1 280px',
            borderRadius: 18,
            padding: '24px 26px',
            background:
              'linear-gradient(135deg, #c96442 0%, #b4543a 55%, #9a3f2c 100%)',
            color: '#fff',
            boxShadow: '0 14px 32px rgba(201,100,66,.30)',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, opacity: 0.85 }}>
            Patrimônio total
          </div>
          <div style={{ ...display, fontSize: 42, lineHeight: 1.05 }}>
            {money(patrimonioTotal)}
          </div>
          {Number(accounts?.summary.reserves ?? '0') > 0 && (
            <div style={{ fontSize: 12.5, opacity: 0.8 }}>
              Em conta: {money(accounts?.summary.cash ?? '0')} · reserva:{' '}
              {money(accounts?.summary.reserves ?? '0')}
            </div>
          )}
          {Number(accounts?.summary.investments ?? '0') > 0 && (
            <div style={{ fontSize: 12.5, opacity: 0.8 }}>
              Investido (fora do saldo): {money(accounts?.summary.investments ?? '0')}
            </div>
          )}
          <div style={{ fontSize: 12.5, opacity: 0.8 }}>
            Fatura do cartão em aberto: {money(accounts?.summary.credit_card ?? '0')}
          </div>
          {banks.length > 0 && (
            <div
              style={{
                marginTop: 10,
                paddingTop: 12,
                borderTop: '1px solid rgba(255,255,255,.22)',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              {banks.map((b) => (
                <div
                  key={b.label}
                  style={{ display: 'flex', alignItems: 'center', gap: 9 }}
                >
                  <img
                    src={b.logo}
                    alt={b.label}
                    width={22}
                    height={22}
                    style={{ width: 22, height: 22, borderRadius: 6, background: '#fff' }}
                  />
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>
                    {b.label}
                  </span>
                  <span style={{ ...display, fontSize: 14 }}>
                    {money(b.total)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <Card className="u-card-hover" style={{ flex: '1 1 180px', display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>
          <span style={chip('var(--ok)')}>
            <IconArrowIn size={18} />
          </span>
          <div>
            <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>
              Entrou <span style={{ fontWeight: 500, opacity: 0.75 }}>· {monthLabel}</span>
            </div>
            <div style={{ ...display, fontSize: 28, color: 'var(--ok)' }}>
              {money(summary?.received ?? '0')}
            </div>
          </div>
        </Card>

        <Card className="u-card-hover" style={{ flex: '1 1 180px', display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>
          <span style={chip('var(--danger)')}>
            <IconArrowOut size={18} />
          </span>
          <div>
            <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>
              Saiu <span style={{ fontWeight: 500, opacity: 0.75 }}>· {monthLabel}</span>
            </div>
            <div style={{ ...display, fontSize: 28, color: 'var(--danger)' }}>
              {money(summary?.spent ?? '0')}
            </div>
          </div>
        </Card>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <Card className="u-card-hover" style={{ flex: '1.6 1 340px', display: 'flex', flexDirection: 'column', height: 264 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>Evolução (líquido mensal)</span>
            <span style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
              {timeline.length} {timeline.length === 1 ? 'mês' : 'meses'}
            </span>
          </div>
          {inflow.length > 0 ? (
            <svg className="u-chartwrap" viewBox="0 0 460 150" preserveAspectRatio="none" style={{ width: '100%', flex: 1, marginTop: 8 }}>
              <defs>
                <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                </linearGradient>
              </defs>
              <line x1="0" y1="130" x2="460" y2="130" stroke="var(--line)" strokeWidth="1" />
              <polygon fill="url(#area)" points={areaPoints(inflow)} />
              <polyline
                fill="none"
                stroke="var(--accent)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={linePoints(inflow)}
              />
              {linePoints(inflow)
                .split(' ')
                .map((pt) => {
                  const [x, y] = pt.split(',')
                  return (
                    <circle
                      key={pt}
                      className="u-chart-dot"
                      cx={x}
                      cy={y}
                      r={4}
                      fill="var(--accent)"
                      stroke="var(--panel)"
                      strokeWidth="2"
                    />
                  )
                })}
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

        <Card className="u-card-hover" style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>Onde foi o dinheiro</span>
            <span style={{ fontSize: 12.5, color: 'var(--ink-soft)' }}>
              {money(summary?.spent ?? '0')}
            </span>
          </div>
          {topCats.length > 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
              <div
                className="u-donut"
                style={{
                  width: 116,
                  height: 116,
                  borderRadius: '50%',
                  background: donut,
                  flexShrink: 0,
                  display: 'grid',
                  placeItems: 'center',
                }}
              >
                <div
                  style={{
                    width: 72,
                    height: 72,
                    background: 'var(--panel)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 11,
                    color: 'var(--ink-soft)',
                    fontWeight: 600,
                  }}
                >
                  {topCats.length} cat.
                </div>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 9 }}>
                {topCats.map((g, i) => (
                  <div key={g.category} className="u-legend" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5 }}>
                    <span style={{ width: 9, height: 9, borderRadius: 3, background: PALETTE[i % PALETTE.length], flexShrink: 0 }} />
                    <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{g.category}</span>
                    <span style={{ color: 'var(--ink-soft)', fontWeight: 600 }}>
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
          recent.items.map((t, i) => (
            <TransactionRow key={t.id} tx={t} borderTop={i > 0} />
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
