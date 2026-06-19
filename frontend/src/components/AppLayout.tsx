import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import {
  IconBolt,
  IconEye,
  IconEyeOff,
  IconHome,
  IconInvest,
  IconMoon,
  IconPower,
  IconSettings,
  IconStatement,
  IconSun,
  IconTarget,
} from '@/components/icons'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'
import { useUi } from '@/lib/ui'

const NAV = [
  { to: '/', label: 'Visão geral', end: true, Icon: IconHome },
  { to: '/investimentos', label: 'Investimentos', Icon: IconInvest },
  { to: '/extrato', label: 'Extrato', Icon: IconStatement },
  { to: '/metas', label: 'Metas', Icon: IconTarget },
  { to: '/config', label: 'Configurações', Icon: IconSettings },
]

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
          pvn<span style={{ color: 'var(--accent)' }}>.</span>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {NAV.map(({ to, label, end, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className="u-nav"
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
              <Icon />
              {label}
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
            aria-label="Sair da conta"
            className="u-ghost"
            style={{
              cursor: 'pointer',
              border: 'none',
              background: 'transparent',
              color: 'var(--ink-soft)',
              display: 'flex',
              padding: 6,
              borderRadius: 8,
            }}
          >
            <IconPower />
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
            padding: '0 26px',
          }}
        >
          <div
            style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}
          >
            <button
              onClick={toggleHide}
              title={hideValues ? 'Mostrar valores' : 'Ocultar valores'}
              aria-label={hideValues ? 'Mostrar valores' : 'Ocultar valores'}
              className="u-ghost"
              style={iconBtn}
            >
              {hideValues ? <IconEyeOff /> : <IconEye />}
            </button>
            <button
              onClick={toggle}
              title="Alternar tema"
              aria-label="Alternar tema claro/escuro"
              className="u-ghost"
              style={iconBtn}
            >
              {theme === 'dark' ? <IconSun /> : <IconMoon />}
            </button>
            <span
              title="Dados via Pluggy"
              style={{
                fontFamily: 'var(--sans)',
                fontWeight: 700,
                fontSize: 12,
                padding: '7px 12px',
                borderRadius: 30,
                background: 'var(--accent2)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <IconBolt size={13} />
              Pluggy
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
