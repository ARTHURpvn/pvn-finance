import type { CSSProperties, ReactNode } from 'react'

export function Card({
  children,
  style,
  dark,
}: {
  children: ReactNode
  style?: CSSProperties
  dark?: boolean
}) {
  return (
    <div
      style={{
        background: dark ? 'var(--dark-card)' : 'var(--panel)',
        color: dark ? 'var(--dark-ink)' : 'var(--ink)',
        border: dark ? 'none' : '1px solid var(--line)',
        borderRadius: 18,
        padding: '18px 20px',
        boxShadow: 'var(--shadow-sm)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}
