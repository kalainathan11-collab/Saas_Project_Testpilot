import { useSyncExternalStore } from 'react'
import { getTheme, setTheme, subscribeTheme, type Theme } from '../lib/theme'

export function useTheme(): { theme: Theme; setTheme: (theme: Theme) => void } {
  const theme = useSyncExternalStore(subscribeTheme, getTheme, () => 'light' as Theme)
  return { theme, setTheme }
}
