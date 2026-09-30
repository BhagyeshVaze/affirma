// Level is shown with an arrow and words, never color alone.
export default function LevelBadge({ level, direction }) {
  if (level === 'unknown') return <span className="badge badge-unknown">No data</span>
  if (level === 'normal') return <span className="badge badge-normal">Normal</span>
  const warm = direction === 'warmer'
  const text = `${level === 'very_unusual' ? 'Very unusual' : 'Unusual'}, ${warm ? 'warm' : 'cool'}`
  return (
    <span className={`badge ${warm ? 'badge-warm' : 'badge-cool'} ${level === 'very_unusual' ? 'badge-strong' : ''}`}>
      <span aria-hidden="true">{warm ? '▲' : '▼'}</span> {text}
    </span>
  )
}
