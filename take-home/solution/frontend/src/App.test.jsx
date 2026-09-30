import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import App from './App.jsx'
import { strongerMeasure } from './format.js'

// Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks.
globalThis.ResizeObserver ??= class { observe() {} unobserve() {} disconnect() {} }

const verdict = (v) => ({ unusual_days: 0, very_unusual_days: 0, days_judged: 7, days_without_forecast: 0, verdict: v })
const comparison = { forecast: 20, normal: 18, p5: 10, p95: 26, anomaly: 2, pct_rank: 60, level: 'normal', direction: 'warmer', n: 70 }

function anomalyResponse(highs, lows) {
  return {
    location: { name: null, latitude: 39.74, longitude: -104.98, timezone: 'America/Denver' },
    units: { temperature: '°F', precipitation: 'in' },
    baseline: { years_requested: 10, years_used: 10, from_year: 2016, to_year: 2025, window_days: 3 },
    week: {
      start: '2026-09-30', end: '2026-10-06', avg_high_anomaly: 1, avg_low_anomaly: 9,
      highs: verdict(highs), lows: verdict(lows),
      rain: { forecast_total: 0, avg_total: 0.3, years_wetter: 5, years_drier: 5, years_compared: 10 },
    },
    days: Array.from({ length: 7 }, (_, i) => ({
      date: `2026-10-0${i + 1}`, high: comparison, low: comparison, rain: { forecast: 0 },
    })),
    warnings: [],
    meta: { upstream_calls: 0, generated_at: '2026-09-30T00:00:00Z' },
  }
}

let highs, lows, fetchMock

beforeEach(() => {
  highs = 'normal'
  lows = 'very_unusual'
  fetchMock = vi.fn(async (url) => {
    const body = String(url).startsWith('/api/weather/anomaly')
      ? anomalyResponse(highs, lows)
      : { error: { code: 'upstream_error', message: 'not needed here', retry_after_s: null } }
    return new Response(JSON.stringify(body), { status: body.error ? 502 : 200 })
  })
  vi.stubGlobal('fetch', fetchMock)
  window.history.replaceState(null, '', '/?lat=39.74&lon=-104.98&name=Denver')
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const chartTitle = () => screen.findByRole('heading', { name: /^Forecast (highs|lows) vs the normal range$/ })
const pressed = (label) => screen.getByRole('button', { name: label }).getAttribute('aria-pressed')

it('picks the stronger verdict: very > somewhat > normal, highs on a tie', () => {
  const week = (h, l) => ({ highs: { verdict: h }, lows: { verdict: l } })
  expect(strongerMeasure(week('normal', 'very_unusual'))).toBe('low')
  expect(strongerMeasure(week('somewhat_unusual', 'normal'))).toBe('high')
  expect(strongerMeasure(week('somewhat_unusual', 'very_unusual'))).toBe('low')
  expect(strongerMeasure(week('very_unusual', 'very_unusual'))).toBe('high')
  expect(strongerMeasure(week('normal', 'normal'))).toBe('high')
  expect(strongerMeasure(week('not_enough_history', 'normal'))).toBe('low') // a verdict beats none
  expect(strongerMeasure(week('not_enough_history', 'somewhat_unusual'))).toBe('low')
})

it('the chart opens on lows when the nights are the unusual part', async () => {
  render(<App />)
  expect((await chartTitle()).textContent).toBe('Forecast lows vs the normal range')
  expect(pressed('Lows')).toBe('true')
})

it("a manual choice sticks when years or units change", async () => {
  render(<App />)
  await chartTitle()
  fireEvent.click(screen.getByRole('button', { name: 'Highs' }))
  expect((await chartTitle()).textContent).toBe('Forecast highs vs the normal range')

  fireEvent.click(screen.getByRole('button', { name: '°C' }))
  fireEvent.change(screen.getByRole('combobox', { name: /compare with/i }), { target: { value: '20' } })
  await screen.findByText(/this week vs/i)
  expect((await chartTitle()).textContent).toBe('Forecast highs vs the normal range')
  expect(pressed('Highs')).toBe('true')
})

it('without a manual choice, the chart follows the verdict when the data changes', async () => {
  render(<App />)
  expect((await chartTitle()).textContent).toBe('Forecast lows vs the normal range')
  highs = 'very_unusual'
  lows = 'normal'
  fireEvent.click(screen.getByRole('button', { name: '°C' }))
  await screen.findByText(/Days: very unusual/)
  expect((await chartTitle()).textContent).toBe('Forecast highs vs the normal range')
})
