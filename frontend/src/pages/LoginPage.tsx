import { GlassCard } from '../components/ui/GlassCard'
import { LoginForm } from '../components/auth/LoginForm'

export default function LoginPage() {
  return (
    <GlassCard static className="space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Sign in</h1>
        <p className="mt-1 text-sm text-slate-600">Log in to TestPilot</p>
      </div>
      <LoginForm />
    </GlassCard>
  )
}
