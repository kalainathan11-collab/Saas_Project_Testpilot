export type Theme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'testpilot_theme'

const listeners = new Set<() => void>()

export function getTheme(): Theme {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

/** Applies the theme to <html data-theme="..."> (styles live in index.css). */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
}

export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // Storage may be unavailable; theme still applies for this session.
  }
  applyTheme(theme)
  listeners.forEach((l) => l())
}

export function subscribeTheme(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

// Apply the persisted theme as soon as this module is first imported.
if (typeof document !== 'undefined') {
  applyTheme(getTheme())
}
