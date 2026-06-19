import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { AuthShell } from '@/components/AuthShell'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const labelStyle: React.CSSProperties = {
  fontSize: 12.5,
  color: 'var(--ink-soft)',
  marginBottom: 6,
  fontWeight: 600,
}
const inputStyle: React.CSSProperties = {
  width: '100%',
  border: '1.5px solid var(--line-2)',
  borderRadius: 12,
  padding: '13px 15px',
  fontSize: 14,
  color: 'var(--ink)',
  background: 'var(--panel-2)',
  fontFamily: 'var(--sans)',
  outline: 'none',
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Falha ao entrar')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell>
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          animation: 'fadeUp .3s ease',
        }}
      >
        <div
          style={{
            fontFamily: 'var(--display)',
            fontWeight: 700,
            fontSize: 28,
            letterSpacing: '-.5px',
          }}
        >
          Bem-vindo de volta
        </div>
        <div>
          <div style={labelStyle}>E-mail</div>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="voce@email.com"
            required
            style={inputStyle}
          />
        </div>
        <div>
          <div style={labelStyle}>Senha</div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            style={inputStyle}
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          style={{
            marginTop: 4,
            cursor: 'pointer',
            fontFamily: 'var(--sans)',
            fontWeight: 700,
            fontSize: 15,
            padding: 14,
            border: 'none',
            borderRadius: 12,
            background: 'var(--accent)',
            color: 'var(--accent-ink)',
            opacity: submitting ? 0.7 : 1,
          }}
        >
          {submitting ? 'Entrando…' : 'Entrar →'}
        </button>
        <div
          style={{
            textAlign: 'center',
            fontSize: 13.5,
            color: 'var(--ink-soft)',
          }}
        >
          Não tem conta?{' '}
          <Link
            to="/register"
            style={{ color: 'var(--accent)', fontWeight: 600 }}
          >
            Criar conta
          </Link>
        </div>
      </form>
    </AuthShell>
  )
}
