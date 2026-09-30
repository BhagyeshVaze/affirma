import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import VerdictBanner from './VerdictBanner.jsx'

afterEach(cleanup)

const verdict = (over) => ({
  unusual_days: 0, very_unusual_days: 0, days_judged: 7, days_without_forecast: 0,
  verdict: 'normal', ...over,
})

function data(highs, lows, days = 7) {
  return {
    week: { highs, lows, avg_high_anomaly: null, avg_low_anomaly: 1.2 },
    days: Array.from({ length: days }, (_, i) => ({ date: `2026-10-0${i + 1}` })),
    baseline: { from_year: 2016, to_year: 2025, years_used: 10, window_days: 3 },
    units: { temperature: '°F', precipitation: 'in' },
    warnings: [],
  }
}

it('blames a missing forecast, not history, when forecast values are missing', () => {
  const highs = verdict({ verdict: 'not_enough_history', days_judged: 0, days_without_forecast: 7 })
  render(<VerdictBanner data={data(highs, verdict())} />)
  expect(screen.getByText(/forecast is missing values for 7 of 7 days/i)).toBeTruthy()
  expect(screen.queryByText(/try more years/i)).toBeNull()
})

it('suggests more years when the history is what is thin', () => {
  const thin = verdict({ verdict: 'not_enough_history', days_judged: 2 })
  render(<VerdictBanner data={data(thin, thin)} />)
  expect(screen.getAllByText(/only 2 of 7 days can be judged/i)).toHaveLength(2)
  expect(screen.getAllByText(/try more years/i)).toHaveLength(2)
})

it('counts against the real number of days, not a fixed 7', () => {
  render(<VerdictBanner data={data(verdict({ unusual_days: 1 }), verdict(), 5)} />)
  expect(screen.getByText(/1 of 5 outside the normal range/i)).toBeTruthy()
})
