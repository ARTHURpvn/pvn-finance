import { useState } from 'react'

interface Point {
  label: string
  value: number
}

const W = 460
const H = 150
const PAD = 12

/** Gráfico de linha/área com tooltip: passa o mouse em cima e mostra o valor
 * do mês. Reusado no Dashboard e em Investimentos. */
export function EvolutionChart({
  points,
  formatValue,
  gradientId,
}: {
  points: Point[]
  formatValue: (n: number) => string
  gradientId: string
}) {
  const [hover, setHover] = useState<number | null>(null)

  if (points.length < 2) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-soft)', fontSize: 13 }}>
        Sem histórico suficiente ainda
      </div>
    )
  }

  const values = points.map((p) => p.value)
  const max = Math.max(...values)
  const min = Math.min(...values, 0)
  const span = max - min || 1
  const coords = values.map((v, i) => ({
    x: (i / (values.length - 1)) * W,
    y: H - PAD - ((v - min) / span) * (H - PAD * 2),
  }))
  const line = coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ')
  const area = `0,${H} ${line} ${W},${H}`

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
    setHover(Math.round(frac * (values.length - 1)))
  }

  const leftPct = (i: number) => (i / (values.length - 1)) * 100
  const topPct = (i: number) => (coords[i].y / H) * 100

  return (
    <div
      style={{ position: 'relative', flex: 1, marginTop: 8, cursor: 'crosshair' }}
      onMouseMove={onMove}
      onMouseLeave={() => setHover(null)}
    >
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ width: '100%', height: '100%', display: 'block' }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.25" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon fill={`url(#${gradientId})`} points={area} />
        <polyline fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" points={line} />
        {hover != null && (
          <line x1={coords[hover].x} y1="0" x2={coords[hover].x} y2={H} stroke="var(--accent)" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
        )}
      </svg>

      {/* Marcador (círculo) na camada HTML — não distorce como no SVG esticado. */}
      {hover != null && (
        <>
          <div
            style={{
              position: 'absolute', left: `${leftPct(hover)}%`, top: `${topPct(hover)}%`,
              width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)',
              border: '2px solid var(--panel)', transform: 'translate(-50%, -50%)', pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute', left: `${leftPct(hover)}%`, top: `${topPct(hover)}%`,
              transform: `translate(${hover > values.length / 2 ? '-108%' : '8%'}, -120%)`,
              background: 'rgba(28,25,23,.96)', color: '#fff', borderRadius: 8,
              padding: '6px 9px', fontSize: 12, lineHeight: 1.3, whiteSpace: 'nowrap',
              pointerEvents: 'none', boxShadow: '0 6px 18px rgba(0,0,0,.22)',
            }}
          >
            <div style={{ opacity: 0.75, fontSize: 11 }}>{points[hover].label}</div>
            <div style={{ fontWeight: 700 }}>{formatValue(points[hover].value)}</div>
          </div>
        </>
      )}
    </div>
  )
}
