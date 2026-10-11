import { EmptyState } from './EmptyState'

/** Suspense fallback shown while a lazily loaded route chunk is fetched. */
export function PageFallback() {
  return (
    <div className="p-6" role="status" aria-live="polite">
      <EmptyState title="Loading..." />
    </div>
  )
}
