import { useEffect, useRef, useState } from 'react'
import { useApi } from '../useApi.js'

export default function CitySearch({ onPick }) {
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const pickedLabel = useRef(null)

  // Search 300 ms after typing stops, with 2+ characters. Skip the label a pick puts in the box.
  useEffect(() => {
    if (text === pickedLabel.current) return
    const id = setTimeout(() => setQuery(text.trim()), 300)
    return () => clearTimeout(id)
  }, [text])

  const search = useApi('/api/cities', query.length >= 2 ? { q: query, count: 6 } : null)
  // Only results for the current query (right after it changes, data is still the old query's).
  const results = search.data?.query === query ? search.data.results : []

  useEffect(() => setActive(0), [search.data])

  function pick(place) {
    onPick(place)
    pickedLabel.current = place.label
    setText(place.label)
    setOpen(false)
  }

  // The list shows only results for what's typed now, and the keyboard acts only on that list.
  const showList = open && query.length >= 2 && text.trim() === query

  function onKeyDown(e) {
    if (!showList || !results.length) {
      if (e.key === 'Enter') e.preventDefault()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((i) => (i + 1) % results.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((i) => (i - 1 + results.length) % results.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      pick(results[active])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="search">
      <label htmlFor="city-search">City</label>
      <input
        id="city-search"
        type="search"
        placeholder="Search a city, e.g. Denver"
        autoComplete="off"
        value={text}
        onChange={(e) => {
          pickedLabel.current = null // the user is typing: forget the last pick
          setText(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={onKeyDown}
        role="combobox"
        aria-expanded={showList}
        aria-controls="city-results"
      />
      {showList && (
        <ul id="city-results" className="search-results" role="listbox">
          {search.status === 'loading' && <li className="search-note">Searching…</li>}
          {search.status === 'error' && <li className="search-note search-error">{search.error.message}</li>}
          {search.status === 'success' && results.length === 0 && (
            <li className="search-note">No places match “{query}”.</li>
          )}
          {results.map((p, i) => (
            <li
              key={p.id ?? `${p.latitude},${p.longitude}`}
              role="option"
              aria-selected={i === active}
              className={i === active ? 'active' : ''}
              onMouseDown={() => pick(p)}
              onMouseEnter={() => setActive(i)}
            >
              {p.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
