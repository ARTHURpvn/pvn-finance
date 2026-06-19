import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'
import { useUi } from '@/lib/ui'

const NAV = [
  { to: '/', label: 'Visão geral', end: true, icon: 'M3 11l9-8 9 8 M5 10v10h5v-6h4v6h5V10' },
  { to: '/investimentos', label: 'Investimentos', icon: 'M4 19V5 M4 19h16 M8 15l3-4 3 2 4-7' },
  { to: '/extrato', label: 'Extrato', icon: 'M8 7h12 M8 12h12 M8 17h12' },
  { to: '/metas', label: 'Metas', icon: '' },
  { to: '/config', label: 'Configurações', icon: 'M4 8h16 M4 16h16' },
]

function Icon({ d }: { d: string }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {d ? (
        d.split(' M').map((seg, i) => <path key={i} d={(i ? 'M' : '') + seg} />)
      ) : (
        <>
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="5" />
          <circle cx="12" cy="12" r="1" />
        </>
      )}
    </svg>
  )
}

export function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const { hideValues, toggleHide } = useUi()

  return (
    <div style={{ height: '100svh', display: 'flex', overflow: 'hidden' }}>
      <aside
        style={{
          width: 236,
          flexShrink: 0,
          background: 'var(--panel)',
          borderRight: '1px solid var(--line)',
          display: 'flex',
          flexDirection: 'column',
          padding: '20px 16px',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--display)',
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: '-.5px',
            padding: '6px 10px 22px',
          }}
        >
          fin<span style={{ color: 'var(--accent)' }}>.</span>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              style={({ isActive }) => ({
                textDecoration: 'none',
                fontFamily: 'var(--sans)',
                fontWeight: 600,
                fontSize: 14,
                padding: '11px 12px',
                borderRadius: 11,
                display: 'flex',
                alignItems: 'center',
                gap: 11,
                background: isActive ? 'var(--fill)' : 'transparent',
                color: isActive ? 'var(--accent)' : 'var(--ink)',
              })}
            >
              <Icon d={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div
          style={{
            marginTop: 'auto',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: 10,
            borderTop: '1px solid var(--line)',
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: '50%',
              background: 'var(--accent)',
              color: 'var(--accent-ink)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: 14,
              textTransform: 'uppercase',
            }}
          >
            {user?.email?.[0] ?? '?'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {user?.email}
            </div>
            <div style={{ fontSize: 11, color: 'var(--ink-soft)' }}>
              conectado · Pluggy
            </div>
          </div>
          <button
            onClick={logout}
            title="Sair"
            style={{
              cursor: 'pointer',
              border: 'none',
              background: 'transparent',
              color: 'var(--ink-soft)',
              fontSize: 16,
              padding: 4,
            }}
          >
            ⏻
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header
          style={{
            height: 66,
            flexShrink: 0,
            borderBottom: '1px solid var(--line)',
            background: 'var(--panel)',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '0 26px',
          }}
        >
          <span
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--accent)',
              padding: '7px 14px',
              border: '1.5px solid var(--accent)',
              borderRadius: 30,
            }}
          >
            Todas as contas
          </span>
          <div
            style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}
          >
            <button
              onClick={toggleHide}
              title="Ocultar valores"
              style={iconBtn}
            >
              {hideValues ? '🙈' : '👁'}
            </button>
            <button onClick={toggle} title="Tema" style={iconBtn}>
              {theme === 'dark' ? '☀' : '☾'}
            </button>
            <span
              style={{
                fontFamily: 'var(--sans)',
                fontWeight: 700,
                fontSize: 12,
                padding: '7px 12px',
                borderRadius: 30,
                background: 'var(--accent2)',
                color: '#fff',
              }}
            >
              ⚡ Pluggy
            </span>
          </div>
        </header>

        <div style={{ flex: 1, overflowY: 'auto', padding: '26px 30px 40px' }}>
          {children}
        </div>
      </main>
    </div>
  )
}

const iconBtn: React.CSSProperties = {
  cursor: 'pointer',
  width: 38,
  height: 36,
  border: '1.5px solid var(--line-2)',
  borderRadius: 10,
  background: 'var(--panel)',
  color: 'var(--ink-soft)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 15,
}
