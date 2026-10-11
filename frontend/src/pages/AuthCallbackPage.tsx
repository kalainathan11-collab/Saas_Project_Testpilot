import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { refreshAccessToken } from '../services/api'
import { clearTokens } from '../lib/storage'
import { useAuth } from '../hooks/useAuth'

/** Landing page for the Google OAuth redirect: exchanges the HttpOnly refresh cookie for an access token. */
export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [failed, setFailed] = useState(false)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true
    // Tokens are never read from the URL; drop anything that was put there.
    window.history.replaceState(null, '', window.location.pathname)
    refreshAccessToken()
      .then(() => refreshUser())
      .then((user) => {
        if (user) navigate('/dashboard', { replace: true })
        else setFailed(true)
      })
      .catch(() => {
        clearTokens()
        setFailed(true)
      })
  }, [navigate, refreshUser])

  if (failed) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
        <p role="alert" className="text-sm text-red-700">
          Google sign-in failed. Please try again.
        </p>
        <a href="/login" className="text-sm font-semibold text-brand-600 hover:underline">
          Back to sign in
        </a>
      </div>
    )
  }
  return (
    <div className="flex min-h-screen items-center justify-center" role="status">
      <p className="text-sm text-slate-600">Signing you in...</p>
    </div>
  )
}
