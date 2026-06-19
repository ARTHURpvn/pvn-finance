import { Card } from '@/components/Card'
import { display } from '@/lib/styles'

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <div style={{ animation: 'fadeUp .32s ease', maxWidth: 880 }}>
      <div style={{ ...display, fontSize: 26, marginBottom: 18 }}>{title}</div>
      <Card style={{ textAlign: 'center', padding: '48px 24px' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🚧</div>
        <div style={{ fontWeight: 700, fontSize: 17 }}>Em breve</div>
        <div style={{ color: 'var(--ink-soft)', fontSize: 13.5, marginTop: 6 }}>
          Esta seção ainda não está disponível no MVP.
        </div>
      </Card>
    </div>
  )
}
