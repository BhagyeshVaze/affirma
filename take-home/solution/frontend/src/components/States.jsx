export function Loading({ label = 'Loading', height = 160 }) {
  return (
    <div className="skeleton" style={{ height }} role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry }) {
  const busy = error?.code === 'upstream_rate_limited'
  return (
    <div className="state state-error" role="alert">
      <strong>{busy ? 'The weather service is busy.' : 'Something went wrong.'}</strong>
      <p>{error?.message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function Empty({ title, children }) {
  return (
    <div className="state">
      <strong>{title}</strong>
      {children}
    </div>
  )
}
