import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Card } from '@/components/Card'
import { IconArrowIn, IconArrowOut } from '@/components/icons'
import { apiFetch } from '@/lib/api'
import { bankOf } from '@/lib/banks'
import { display } from '@/lib/styles'
import { useUi } from '@/lib/ui'
import type { InvestmentDetail, InvestmentsResponse } from '@/lib/types'

// ---- helpers de gráfico (linha + área), iguais aos do Dashboard ----
function linePoints(values: number[], w = 460, h = 150, pad = 12): string {
  if (values.length === 0) return ''
  const max = Math.max(...values)
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
  return pts ? `0,150 ${pts} 460,150` : ''
}

const TYPE_LABEL: Record<string, string> = {
  FIXED_INCOME: 'Renda fixa',
  EQUITY: 'Ação / FII',
  ETF: 'ETF',
  MUTUAL_FUND: 'Fundo',
  SECURITY: 'Previdência',
  COE: 'COE',
}
const MES_CURTO = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function monthLabel(ym: string): string {
  const [, m] = ym.split('-')
  return MES_CURTO[Number(m) - 1] ?? ym
}

/** Avatar do banco: logo se houver, senão monograma com a inicial. */
function BankAvatar({ label, size = 26 }: { label: string; size?: number }) {
  const bank = bankOf(label)
  const [failed, setFailed] = useState(false)
  if (bank && !failed) {
    return (
      <img
        src={bank.logo}
        alt={label}
        width={size}
        height={size}
        onError={() => setFailed(true)}
        style={{ width: size, height: size, borderRadius: 7, background: '#fff', border: '1px solid var(--line)' }}
      />
    )
  }
  return (
    <span
      style={{
        width: size, height: size, borderRadius: 7, flexShrink: 0,
        background: 'var(--accent)', color: '#fff', fontWeight: 700,
        fontSize: size * 0.5, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      {label.charAt(0).toUpperCase()}
    </span>
  )
}

function chip(color: string): React.CSSProperties {
  return {
    width: 34, height: 34, borderRadius: 10,
    background: `color-mix(in srgb, ${color} 16%, transparent)`,
    color, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
  }
}

export function InvestimentosPage() {
  const { money } = useUi()
  const [data, setData] = useState<InvestmentsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<InvestmentsResponse>('/investments')
      .then(setData)
      .catch(() => toast.error('Falha ao carregar os investimentos'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ color: 'var(--ink-soft)' }}>Carregando…</p>

  if (!data || data.investments.length === 0) {
    return (
      <div style={{ ...display, fontSize: 22 }}>
        Investimentos
        <p style={{ ...display, fontSize: 14, color: 'var(--ink-soft)', marginTop: 12, fontWeight: 500 }}>
          Nenhum investimento ainda. Conecte um banco/corretora em Configurações.
        </p>
      </div>
    )
  }

  const { summary, investments, evolution } = data
  const profit = Number(summary.total_profit)
  const evoValues = evolution.map((p) => Number(p.total))

  // Agrupamento por banco.
  const banks = (() => {
    const map = new Map<string, { label: string; total: number }>()
    for (const i of investments) {
      const label = i.bank || 'Outros'
      const cur = map.get(label) ?? { label, total: 0 }
      cur.total += Number(i.balance)
      map.set(label, cur)
    }
    const total = investments.reduce((a, i) => a + Number(i.balance), 0) || 1
    return [...map.values()]
      .map((b) => ({ ...b, pct: Math.round((b.total / total) * 100) }))
      .sort((a, b) => b.total - a.total)
  })()

  // Posições ordenadas por valor.
  const positions = [...investments].sort((a, b) => Number(b.balance) - Number(a.balance))

  return (
    <div style={{ animation: 'fadeUp .32s ease', display: 'flex', flexDirection: 'column', gap: 18, width: '100%', maxWidth: 1180 }}>
      <div style={{ ...display, fontSize: 26 }}>Investimentos</div>

      {/* Resumo */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div
          className="u-card-hover"
          style={{
            flex: '1.5 1 280px', borderRadius: 18, padding: '24px 26px',
            background: 'linear-gradient(135deg, #c96442 0%, #b4543a 55%, #9a3f2c 100%)',
            color: '#fff', boxShadow: '0 14px 32px rgba(201,100,66,.30)',
            display: 'flex', flexDirection: 'column', gap: 4, justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 600, opacity: 0.85 }}>Total investido</div>
          <div style={{ ...display, fontSize: 42, lineHeight: 1.05 }}>{money(summary.total_invested)}</div>
          <div style={{ fontSize: 12.5, opacity: 0.85 }}>
            {positions.length} {positions.length === 1 ? 'posição' : 'posições'} em {banks.length}{' '}
            {banks.length === 1 ? 'instituição' : 'instituições'}
          </div>
        </div>

        <Card className="u-card-hover" style={{ flex: '1 1 190px', display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>
          <span style={chip(profit >= 0 ? 'var(--ok)' : 'var(--danger)')}>
            {profit >= 0 ? <IconArrowIn size={18} /> : <IconArrowOut size={18} />}
          </span>
          <div>
            <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>
              {profit >= 0 ? 'Ganho' : 'Perda'}
            </div>
            <div style={{ ...display, fontSize: 26, color: profit >= 0 ? 'var(--ok)' : 'var(--danger)' }}>
              {money(summary.total_profit)}
            </div>
          </div>
        </Card>

        <Card className="u-card-hover" style={{ flex: '1 1 190px', display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'center' }}>
          <span style={chip('var(--gold)')}>%</span>
          <div>
            <div style={{ fontSize: 13, color: 'var(--ink-soft)', fontWeight: 600 }}>Renda fixa / mês</div>
            <div style={{ ...display, fontSize: 26, color: 'var(--gold)' }}>{money(summary.monthly_income)}</div>
            <div style={{ fontSize: 11, color: 'var(--ink-soft)' }}>estimativa · CDI {summary.cdi_annual_rate}%</div>
          </div>
        </Card>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {/* Evolução */}
        <Card className="u-card-hover" style={{ flex: '1.6 1 340px', display: 'flex', flexDirection: 'column', height: 264 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontWeight: 700, fontSize: 16 }}>Evolução do investido</span>
            <span style={{ fontSize: 11.5, color: 'var(--ink-soft)' }}>estimativa mês a mês</span>
          </div>
          {evoValues.length > 1 ? (
            <svg className="u-chartwrap" viewBox="0 0 460 150" preserveAspectRatio="none" style={{ width: '100%', flex: 1, marginTop: 8 }}>
              <defs>
                <linearGradient id="evoArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                </linearGradient>
              </defs>
              <polygon fill="url(#evoArea)" points={areaPoints(evoValues)} />
              <polyline fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" points={linePoints(evoValues)} />
            </svg>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-soft)', fontSize: 13 }}>
              Sem histórico suficiente ainda
            </div>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--ink-soft)' }}>
            {evolution.map((p) => <span key={p.month}>{monthLabel(p.month)}</span>)}
          </div>
        </Card>

        {/* Por banco */}
        <Card className="u-card-hover" style={{ flex: '1 1 300px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <span style={{ fontWeight: 700, fontSize: 16 }}>Onde está aplicado</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {banks.map((b) => (
              <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <BankAvatar label={b.label} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{b.label}</div>
                  <div style={{ height: 5, borderRadius: 3, background: 'var(--line)', marginTop: 4, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${b.pct}%`, background: 'var(--accent)' }} />
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 13.5, fontWeight: 700 }}>{money(b.total)}</div>
                  <div style={{ fontSize: 11, color: 'var(--ink-soft)' }}>{b.pct}%</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Posições */}
      <Card>
        <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>Minhas posições</div>
        {positions.map((p, i) => (
          <PositionRow key={`${p.name}-${i}`} p={p} borderTop={i > 0} money={money} />
        ))}
      </Card>
    </div>
  )
}

function PositionRow({
  p,
  borderTop,
  money,
}: {
  p: InvestmentDetail
  borderTop: boolean
  money: (v: string | number) => string
}) {
  const profit = p.profit != null ? Number(p.profit) : null
  const rateTxt =
    p.rate != null && p.rate_type
      ? `${Number(p.rate)}% do ${p.rate_type}`
      : p.annual_rate != null
        ? `${Number(p.annual_rate).toFixed(1)}% a.a.`
        : null
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 2px', borderTop: borderTop ? '1px solid var(--line)' : 'none' }}>
      <BankAvatar label={p.bank || 'Outros'} size={30} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.name}</div>
        <div style={{ fontSize: 12, color: 'var(--ink-soft)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <span>{TYPE_LABEL[p.type] ?? p.type}</span>
          {p.bank && <span>· {p.bank}</span>}
          {rateTxt && <span>· {rateTxt}</span>}
          {p.due_date && <span>· vence {p.due_date.slice(8, 10)}/{p.due_date.slice(5, 7)}/{p.due_date.slice(0, 4)}</span>}
        </div>
      </div>
      <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
        <div style={{ fontWeight: 700, fontSize: 14 }}>{money(p.balance)}</div>
        {p.amount_original != null && (
          <div style={{ fontSize: 11.5, color: 'var(--ink-soft)' }}>
            aplicou {money(p.amount_original)}
          </div>
        )}
        {profit != null && (
          <div style={{ fontSize: 11.5, fontWeight: 600, color: profit >= 0 ? 'var(--ok)' : 'var(--danger)' }}>
            {profit >= 0 ? '+' : ''}{money(p.profit as string)}
          </div>
        )}
      </div>
    </div>
  )
}
