import { PageWrapper } from '../layout/PageWrapper'
import { EmptyState } from './EmptyState'

interface PlaceholderPageProps {
  title: string
  description: string
}

/** Stand-in used until the Phase 2 module implements the real page. */
export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <PageWrapper title={title} subtitle={description}>
      <EmptyState title="Coming in Phase 2" description={`${title} will be implemented in its module.`} />
    </PageWrapper>
  )
}
