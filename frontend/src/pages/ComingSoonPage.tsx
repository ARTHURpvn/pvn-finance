import { Card } from '@/components/Card'
import { IconTarget } from '@/components/icons'
import { display } from '@/lib/styles'

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <div
      style={{
        animation: 'fadeUp .32s ease',
        width: '100%',
        maxWidth: 460,
        margin: 'auto',
        textAlign: 'center',
      }}
    >
      <div style={{ ...display, fontSize: 26, marginBottom: 18 }}>{title}</div>
      <Card style={{ padding: '52px 28px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
        <span
          style={{
            width: 64,
            height: 64,
            borderRadius: 18,
            background: 'color-mix(in srgb, var(--accent) 14%, transparent)',
            color: 'var(--accent)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <IconTarget size={30} />
        </span>
        <div style={{ fontWeight: 700, fontSize: 18 }}>Em breve</div>
        <div style={{ color: 'var(--ink-soft)', fontSize: 13.5, maxWidth: 300 }}>
          Esta seção ainda não está disponível no MVP — estamos trabalhando nela.
        </div>
      </Card>
    </div>
  )
}
