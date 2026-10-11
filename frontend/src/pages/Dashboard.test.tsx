import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import SettingsPage from './SettingsPage'

describe('SettingsPage theme toggle', () => {
  it('toggles and persists the theme', async () => {
    render(<SettingsPage />)
    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')
    toggle.click()
    await screen.findByText(/dark theme/i)
    expect(localStorage.getItem('testpilot_theme')).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })
})
