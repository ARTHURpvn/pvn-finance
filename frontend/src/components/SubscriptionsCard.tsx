import { useState } from 'react'
import { Card } from '@/components/Card'
import { useUi } from '@/lib/ui'
import type { Subscription } from '@/lib/types'

/** Logo da assinatura: usa /subs/<slug>.svg; se não existir (ou slug vazio),
 * cai num avatar-monograma na cor da marca. */
function SubLogo({ sub }: { sub: Subscription }) {
  const [failed, setFailed] = useState(false)
  const showImg = Boolean(sub.slug) && !failed
  return (
    <div
      style={{
        width: 38,
        height: 38,
        borderRadius: 11,
        background: showImg ? '#fff' : sub.color,
        border: '1px solid var(--line)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {showImg ? (
        <img
          src={`/subs/${sub.slug}.svg`}
          alt={sub.name}
          width={20}
          height={20}
          onError={() => setFailed(true)}
          style={{ width: 20, height: 20 }}
        />
      ) : (
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>
          {sub.name.charAt(0).toUpperCase()}
        </span>
      )}
    </div>
  )
}

export function SubscriptionsCard({
  subscriptions,
  monthlyTotal,
}: {
  subscriptions: Subscription[]
  monthlyTotal: string
}) {
  const { money } = useUi()
  if (subscriptions.length === 0) return null

  return (
    <Card>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: 10,
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 16 }}>Assinaturas mensais</span>
        <span style={{ fontSize: 13, color: 'var(--ink-soft)' }}>
          {money(monthlyTotal)}<span style={{ opacity: 0.7 }}>/mês</span>
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {subscriptions.map((s, i) => (
          <div
            key={s.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '10px 2px',
              borderTop: i > 0 ? '1px solid var(--line)' : 'none',
            }}
          >
            <SubLogo sub={s} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{s.name}</div>
              <div style={{ fontSize: 12, color: 'var(--ink-soft)' }}>
                {s.months} {s.months === 1 ? 'mês' : 'meses'}
                {s.category ? ` · ${s.category}` : ''}
              </div>
            </div>
            <div style={{ fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap' }}>
              {money(s.monthly_amount)}
              <span style={{ fontSize: 11, color: 'var(--ink-soft)', fontWeight: 500 }}>
                /mês
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
