import { Outlet } from 'react-router-dom'
import { MeshBackground } from './MeshBackground'

/** Layout for unauthenticated pages (login / register). */
export function AuthLayout() {
  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <MeshBackground />
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  )
}
