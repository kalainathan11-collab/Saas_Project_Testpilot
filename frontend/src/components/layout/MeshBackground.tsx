export function MeshBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-indigo-50" />
      <div className="absolute left-1/4 top-0 h-96 w-96 animate-pulse rounded-full bg-purple-200 opacity-30 blur-3xl" />
      <div className="absolute bottom-0 right-1/4 h-96 w-96 animate-pulse rounded-full bg-indigo-200 opacity-30 blur-3xl" />
    </div>
  )
}
