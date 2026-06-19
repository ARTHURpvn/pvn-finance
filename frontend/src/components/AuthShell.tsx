import type { ReactNode } from 'react'

/** Card dividido do protótipo: painel escuro à esquerda + conteúdo à direita. */
export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        minHeight: '100svh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        animation: 'fadeIn .3s ease',
      }}
    >
      <div
        style={{
          width: 940,
          maxWidth: '100%',
          minHeight: 580,
          display: 'flex',
          background: 'var(--panel)',
          border: '1px solid var(--line)',
          borderRadius: 24,
          boxShadow: 'var(--shadow)',
          overflow: 'hidden',
        }}
      >
        <div
          className="auth-aside"
          style={{
            width: 380,
            background: 'var(--dark-card)',
            color: 'var(--dark-ink)',
            padding: '40px 36px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <div
            style={{
              fontFamily: 'var(--display)',
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: '-.5px',
            }}
          >
            fin<span style={{ color: 'var(--accent)' }}>.</span>
          </div>
          <div>
            <div
              style={{
                fontFamily: 'var(--display)',
                fontWeight: 700,
                fontSize: 34,
                lineHeight: 1.15,
                letterSpacing: '-1px',
              }}
            >
              Suas finanças,
              <br />
              num só lugar.
            </div>
            <div
              style={{
                fontSize: 14,
                color: 'var(--dark-soft)',
                marginTop: 14,
                lineHeight: 1.5,
              }}
            >
              Conecte seus bancos via Pluggy e acompanhe gastos automaticamente,
              em tempo real.
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              fontSize: 13.5,
              color: 'var(--dark-soft)',
            }}
          >
            <span>✓ Conexão segura via Pluggy</span>
            <span>✓ Gastos categorizados sozinhos</span>
            <span>✓ Tudo num só painel</span>
          </div>
        </div>

        <div
          style={{
            flex: 1,
            padding: '46px 48px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
