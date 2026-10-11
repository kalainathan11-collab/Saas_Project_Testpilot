import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FormField, fieldControlClass } from '../ui/FormField'
import { GradientButton } from '../ui/GradientButton'
import { GoogleLoginButton } from './GoogleLoginButton'
import { useAuth } from '../../hooks/useAuth'
import { errorMessage, register } from '../../services/authService'

export function RegisterForm() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | undefined>()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 10) {
      setPasswordError('Password must be at least 10 characters.')
      return
    }
    setPasswordError(undefined)
    setSubmitting(true)
    try {
      await register({ email: email.trim(), password, full_name: fullName.trim() })
      await login(email.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Could not create your account.'))
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
      <FormField label="Full name" required>
        <input
          type="text"
          autoComplete="name"
          className={fieldControlClass}
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
      </FormField>
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
      <FormField label="Password" required hint="At least 10 characters" error={passwordError}>
        <input
          type="password"
          autoComplete="new-password"
          className={fieldControlClass}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </FormField>
      <GradientButton
        type="submit"
        className="w-full"
        disabled={submitting || !email || !password || !fullName}
      >
        {submitting ? 'Creating account...' : 'Create account'}
      </GradientButton>
      <GoogleLoginButton label="Sign up with Google" />
      <p className="text-center text-sm text-slate-600">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-brand-600 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  )
}
