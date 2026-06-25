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
  padding: '12px 15px',
  fontSize: 14,
  color: 'var(--ink)',
  background: 'var(--panel-2)',
  fontFamily: 'var(--sans)',
  outline: 'none',
}

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await register(email, password)
      navigate('/')
    } catch (error) {
      toast.error(
        error instanceof ApiError ? error.message : 'Falha ao criar conta',
      )
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
          gap: 14,
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
          Criar conta
        </div>
        <div>
          <div style={labelStyle}>E-mail</div>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="voce@email.com"
            required
            className="u-field"
            style={inputStyle}
          />
        </div>
        <div>
          <div style={labelStyle}>Senha</div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="mínimo 8 caracteres"
            minLength={8}
            required
            className="u-field"
            style={inputStyle}
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="u-solid"
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
          {submitting ? 'Criando…' : 'Criar conta e conectar banco →'}
        </button>
        <div
          style={{
            textAlign: 'center',
            fontSize: 13.5,
            color: 'var(--ink-soft)',
          }}
        >
          Já tem conta?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>
            Entrar
          </Link>
        </div>
      </form>
    </AuthShell>
  )
}
