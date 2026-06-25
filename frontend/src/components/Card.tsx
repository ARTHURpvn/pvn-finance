import type { CSSProperties, ReactNode } from 'react'

export function Card({
  children,
  style,
  dark,
  className,
}: {
  children: ReactNode
  style?: CSSProperties
  dark?: boolean
  className?: string
}) {
  return (
    <div
      className={className}
      style={{
        background: dark ? 'var(--dark-card)' : 'var(--panel)',
        color: dark ? 'var(--dark-ink)' : 'var(--ink)',
        border: dark ? 'none' : '1px solid var(--line)',
        borderRadius: 18,
        padding: '24px 26px',
        boxShadow: 'var(--shadow-sm)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}
