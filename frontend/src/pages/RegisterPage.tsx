import { GlassCard } from '../components/ui/GlassCard'
import { RegisterForm } from '../components/auth/RegisterForm'

export default function RegisterPage() {
  return (
    <GlassCard static className="space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
        <p className="mt-1 text-sm text-slate-600">Start managing your testing with TestPilot</p>
      </div>
      <RegisterForm />
    </GlassCard>
  )
}
