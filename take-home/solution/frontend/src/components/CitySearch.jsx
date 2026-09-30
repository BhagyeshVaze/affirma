import { useEffect, useRef, useState } from 'react'
import { useApi } from '../useApi.js'

export default function CitySearch({ onPick }) {
  const [text, setText] = useState('')
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const pickedLabel = useRef(null)

  // debounce: search 300 ms after typing stops, and only with 2+ characters.
  // After a pick, the box shows the place's label; that is not something to search for.
  useEffect(() => {
    if (text === pickedLabel.current) return
    const id = setTimeout(() => setQuery(text.trim()), 300)
    return () => clearTimeout(id)
  }, [text])

  const search = useApi('/api/cities', query.length >= 2 ? { q: query, count: 6 } : null)
  // only results for the current query; on the first render after the query changes,
  // search.data still holds the previous query's results
  const results = search.data?.query === query ? search.data.results : []

  useEffect(() => setActive(0), [search.data])

  function pick(place) {
    onPick(place)
    pickedLabel.current = place.label
    setText(place.label)
    setOpen(false)
  }

  // The list only shows results for what is typed now. While the next search is pending
  // (debounce), the old results are hidden, and the keyboard must not act on them.
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
          pickedLabel.current = null // the user is typing now; search whatever they type
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
