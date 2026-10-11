import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge, StatusBadge } from './Badge'
import { DataTable } from './DataTable'
import { KpiCard } from './KpiCard'

describe('base UI components', () => {
  it('renders a badge', () => {
    render(<Badge tone="green">Ready</Badge>)
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('renders a status badge', () => {
    render(<StatusBadge value="Failed" />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders KPI label and value', () => {
    render(<KpiCard label="Pass rate" value="92%" />)
    expect(screen.getByText('Pass rate')).toBeInTheDocument()
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('shows empty state when there are no rows', () => {
    render(<DataTable<{ id: number }> columns={[]} rows={[]} rowKey={(r) => r.id} emptyTitle="No data" />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })
})
