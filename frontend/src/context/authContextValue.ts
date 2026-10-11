import { createContext } from 'react'
import type { User } from '../types'

export interface AuthContextValue {
  user: User | null
  /** True while the initial session check is running. */
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  /** Re-fetch the current user (e.g. after OAuth callback). Resolves to null if not signed in. */
  refreshUser: () => Promise<User | null>
  setUser: (user: User | null) => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
