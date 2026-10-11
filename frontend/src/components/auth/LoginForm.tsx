import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FormField, fieldControlClass } from '../ui/FormField'
import { GradientButton } from '../ui/GradientButton'
import { GoogleLoginButton } from './GoogleLoginButton'
import { useAuth } from '../../hooks/useAuth'
import { errorMessage } from '../../services/authService'

export function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Invalid email or password.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      {error && (
        <p role="alert" className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <FormField label="Email" required>
        <input
          type="email"
          autoComplete="email"
          className={fieldControlClass}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </FormField>
      <FormField label="Password" required>
        <input
          type="password"
          autoComplete="current-password"
          className={fieldControlClass}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </FormField>
      <GradientButton type="submit" className="w-full" disabled={submitting || !email || !password}>
        {submitting ? 'Signing in...' : 'Sign in'}
      </GradientButton>
      <GoogleLoginButton />
      <p className="text-center text-sm text-slate-600">
        No account?{' '}
        <Link to="/register" className="font-semibold text-brand-600 hover:underline">
          Create one
        </Link>
      </p>
    </form>
  )
}
