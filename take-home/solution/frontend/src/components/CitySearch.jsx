import { useEffect, useState } from 'react'
import { useApi } from '../useApi.js'

export default function CitySearch({ onPick }) {
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)

  // debounce: search 300 ms after typing stops, and only with 2+ characters
  useEffect(() => {
    const id = setTimeout(() => setQuery(text.trim()), 300)
    return () => clearTimeout(id)
  }, [text])

  const search = useApi('/api/cities', query.length >= 2 ? { q: query, count: 6 } : null)
  const results = search.data?.results ?? []

  useEffect(() => setActive(0), [search.data])

  function pick(place) {
    onPick(place)
    setText(place.label)
    setOpen(false)
  }

  function onKeyDown(e) {
    if (!open || !results.length) return
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

  const showList = open && query.length >= 2 && text.trim() === query

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
