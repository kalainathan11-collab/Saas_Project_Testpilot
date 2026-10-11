import { useState, type FormEvent } from 'react'
import { GlassCard } from '../components/ui/GlassCard'
import { GradientButton } from '../components/ui/GradientButton'
import { FormField, fieldControlClass } from '../components/ui/FormField'
import { useAuth } from '../hooks/useAuth'
import { errorMessage, updateMe } from '../services/authService'

export default function ProfilePage() {
  const { user, setUser } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'ok' | 'error'; text: string } | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      setUser(await updateMe(fullName.trim()))
      setMessage({ type: 'ok', text: 'Profile updated.' })
    } catch (err) {
      setMessage({ type: 'error', text: errorMessage(err, 'Could not update your profile.') })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-600">Manage your account</p>
      </div>
      <GlassCard static>
        <form onSubmit={onSubmit} className="space-y-4">
          {message && (
            <p
              role={message.type === 'error' ? 'alert' : 'status'}
              className={
                message.type === 'error'
                  ? 'rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700'
                  : 'rounded-xl bg-green-50 px-3 py-2 text-sm text-green-700'
              }
            >
              {message.text}
            </p>
          )}
          <FormField label="Email" hint="Email cannot be changed">
            <input className={fieldControlClass} value={user?.email ?? ''} readOnly disabled />
          </FormField>
          <FormField label="Full name" required>
            <input
              className={fieldControlClass}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </FormField>
          <GradientButton type="submit" disabled={saving || !fullName.trim()}>
            {saving ? 'Saving...' : 'Save changes'}
          </GradientButton>
        </form>
      </GlassCard>
    </div>
  )
}
