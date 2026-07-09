import { IconArrowIn, IconArrowOut } from '@/components/icons'
import { bankOf } from '@/lib/banks'
import { useUi } from '@/lib/ui'
import type { Transaction } from '@/lib/types'

/** Linha de transação compartilhada entre Extrato e Visão geral.
 * Mostra a logo do banco de origem, a direção (entrada/saída/cartão) por cor
 * e um badge de seta, e o valor. */
export function TransactionRow({
  tx,
  onClick,
  borderTop,
}: {
  tx: Transaction
  onClick?: () => void
  borderTop?: boolean
}) {
  const { money } = useUi()
  const income = tx.direction === 'in'
  const isCard = tx.account_type === 'credit_card'
  // Cartão de crédito (gasto) em laranja; entrada verde; saída débito vermelho.
  const tone =
    isCard && !income ? 'var(--gold)' : income ? 'var(--ok)' : 'var(--danger)'
  const bank = bankOf(tx.account_name)

  return (
    <div
      onClick={onClick}
      className="u-row"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 18px',
        borderTop: borderTop ? '1px solid var(--line)' : 'none',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <span style={{ position: 'relative', flexShrink: 0 }}>
        {bank ? (
          <img
            src={bank.logo}
            alt={bank.label}
            width={40}
            height={40}
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              objectFit: 'cover',
              border: '1px solid var(--line)',
              background: 'var(--panel)',
            }}
          />
        ) : (
          <span
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: `color-mix(in srgb, ${tone} 14%, transparent)`,
              color: tone,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {income ? <IconArrowIn size={18} /> : <IconArrowOut size={18} />}
          </span>
        )}
        {/* Badge de direção sobre a logo do banco */}
        {bank && (
          <span
            style={{
              position: 'absolute',
              right: -4,
              bottom: -4,
              width: 18,
              height: 18,
              borderRadius: '50%',
              background: tone,
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid var(--panel)',
            }}
          >
            {income ? <IconArrowIn size={10} /> : <IconArrowOut size={10} />}
          </span>
        )}
      </span>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 600,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {tx.description}
        </div>
        <div style={{ marginTop: 3, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: 11.5,
              color: 'var(--ink-soft)',
              background: 'var(--fill)',
              padding: '2px 8px',
              borderRadius: 20,
              fontWeight: 600,
            }}
          >
            {tx.category_name ?? 'Sem categoria'}
          </span>
          {isCard && (
            <span
              style={{
                fontSize: 11.5,
                color: 'var(--gold)',
                background: 'color-mix(in srgb, var(--gold) 15%, transparent)',
                padding: '2px 8px',
                borderRadius: 20,
                fontWeight: 700,
              }}
            >
              cartão
            </span>
          )}
        </div>
      </div>

      <span
        style={{
          fontFamily: 'var(--display)',
          fontWeight: 700,
          fontSize: 15,
          whiteSpace: 'nowrap',
          color: tone,
        }}
      >
        {money(tx.amount)}
      </span>
    </div>
  )
}
