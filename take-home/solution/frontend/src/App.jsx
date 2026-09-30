import { useState } from 'react'
import { strongerMeasure } from './format.js'
import { useApi } from './useApi.js'
import CitySearch from './components/CitySearch.jsx'
import { Segmented, YearsSelect } from './components/Controls.jsx'
import DayTable from './components/DayTable.jsx'
import RainCard from './components/RainCard.jsx'
import SameWeekChart from './components/SameWeekChart.jsx'
import { Empty, ErrorState, Loading } from './components/States.jsx'
import VerdictBanner from './components/VerdictBanner.jsx'
import WeekChart from './components/WeekChart.jsx'

// Quick picks for the empty state. Coordinates are from our own /api/cities search.
const EXAMPLES = [
  { label: 'Denver, Colorado, United States', latitude: 39.74, longitude: -104.98 },
  { label: 'Chicago, Illinois, United States', latitude: 41.85, longitude: -87.65 },
  { label: 'Phoenix, Arizona, United States', latitude: 33.45, longitude: -112.07 },
  { label: 'London, England, United Kingdom', latitude: 51.51, longitude: -0.13 },
]

// A picked city is kept in the URL (?lat=..&lon=..&name=..) so a view can be shared or reloaded.
function placeFromUrl() {
  const q = new URLSearchParams(window.location.search)
  if (!q.has('lat') || !q.has('lon')) return null
  const lat = Number(q.get('lat'))
  const lon = Number(q.get('lon'))
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null
  return { label: q.get('name') || `${lat}, ${lon}`, latitude: lat, longitude: lon }
}

function placeToUrl(p) {
  const q = new URLSearchParams({ lat: p.latitude, lon: p.longitude, name: p.label })
  window.history.replaceState(null, '', `?${q}`)
}

export default function App() {
  const [place, setPlaceState] = useState(placeFromUrl)
  const setPlace = (p) => {
    setPlaceState(p)
    setMeasureChoice(null) // a new city starts on its own stronger verdict
    placeToUrl(p)
  }
  const [years, setYears] = useState(10)
  const [units, setUnits] = useState('imperial')
  // The data lives here so the chart and its toggle read the same value in the same render.
  const params = place ? { lat: place.latitude, lon: place.longitude, years, units } : null
  const anomaly = useApi('/api/weather/anomaly', params)
  const sameWeek = useApi('/api/weather/same-week', params)

  // The chart shows the user's pick if they made one, else the stronger of highs and lows.
  const [measureChoice, setMeasureChoice] = useState(null)
  const measure = measureChoice ?? (anomaly.data ? strongerMeasure(anomaly.data.week) : 'high')

  return (
    <div className="page">
      <header className="header">
        <h1>Is this week unusual?</h1>
        <p className="subtitle">
          The next 7 days of forecast weather, compared with the same dates in past years.
        </p>
      </header>

      <div className="controls">
        <CitySearch onPick={setPlace} />
        <YearsSelect value={years} onChange={setYears} />
        <Segmented
          label="Units"
          value={units}
          onChange={setUnits}
          options={[{ value: 'imperial', label: '°F' }, { value: 'metric', label: '°C' }]}
        />
        <Segmented
          label="Chart"
          value={measure}
          onChange={setMeasureChoice}
          options={[{ value: 'high', label: 'Highs' }, { value: 'low', label: 'Lows' }]}
        />
      </div>

      {place ? (
        <Dashboard place={place} anomaly={anomaly} sameWeek={sameWeek} measure={measure} />
      ) : (
        <Empty title="Search for a city to begin.">
          <p>Or try one of these:</p>
          <div className="chips">
            {EXAMPLES.map((p) => (
              <button key={p.label} type="button" onClick={() => setPlace(p)}>
                {p.label.split(',')[0]}
              </button>
            ))}
          </div>
        </Empty>
      )}

      <footer className="footer">
        Data: <a href="https://open-meteo.com/">Open-Meteo</a>. Normals come from historical reanalysis
        for the selected years, not an official 30-year climate normal. The forecast and the history
        come from different models: they agree within about 2°F (1°C) on average, but can differ by several
        degrees on a single day, so treat small differences with care.
      </footer>
    </div>
  )
}

function Dashboard({ place, anomaly, sameWeek, measure }) {
  const retryAll = () => {
    anomaly.retry()
    sameWeek.retry()
  }

  return (
    <main className="dashboard">
      <h2 className="place">{place.label}</h2>
      {anomaly.status === 'loading' && (
        <>
          <Loading label="Loading this week" height={150} />
          <Loading label="Loading chart" height={340} />
        </>
      )}
      {anomaly.status === 'error' && <ErrorState error={anomaly.error} onRetry={retryAll} />}
      {anomaly.status === 'success' && (
        <>
          <VerdictBanner data={anomaly.data} />
          <WeekChart data={anomaly.data} measure={measure} />
          <div className="grid-2">
            <SameWeekChart request={sameWeek} />
            <RainCard data={anomaly.data} />
          </div>
          <DayTable data={anomaly.data} />
          <p className="note">
            Upstream calls for this view: {anomaly.data.meta.upstream_calls}
            {anomaly.data.meta.upstream_calls === 0 && ' (served from cache)'}
          </p>
        </>
      )}
    </main>
  )
}
