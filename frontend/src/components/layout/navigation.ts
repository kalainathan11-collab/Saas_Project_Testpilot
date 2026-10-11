export interface NavItem {
  to: string
  label: string
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/projects', label: 'Projects' },
  { to: '/requirements', label: 'Requirements' },
  { to: '/testcases', label: 'Test Cases' },
  { to: '/testruns', label: 'Test Runs' },
  { to: '/defects', label: 'Defects' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
]
