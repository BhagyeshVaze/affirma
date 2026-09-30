import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import CitySearch from './CitySearch.jsx'

const place = (label, latitude, longitude) => ({
  id: latitude, label, name: label.split(',')[0], admin1: null, country: null, country_code: null,
  latitude, longitude, timezone: null, population: null,
})
const OREGON = place('Portland, Oregon, United States', 45.52, -122.68)
const MAINE = place('Portland, Maine, United States', 43.66, -70.26)

let fetchMock

beforeEach(() => {
  // stand-in for our backend's /api/cities
  fetchMock = vi.fn(async (url) => {
    const q = new URL(url, 'http://test').searchParams.get('q')
    const results = q === 'Portland' ? [OREGON] : q === 'Portland, Maine' ? [MAINE] : []
    return new Response(JSON.stringify({ query: q, results }), { status: 200 })
  })
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const queries = () => fetchMock.mock.calls.map(([url]) => new URL(url, 'http://test').searchParams.get('q'))

function setup() {
  const onPick = vi.fn()
  render(<CitySearch onPick={onPick} />)
  const input = screen.getByRole('combobox')
  fireEvent.focus(input)
  return { onPick, input }
}

it('Enter does not pick a stale result the user can no longer see (review bug 2)', async () => {
  const { onPick, input } = setup()
  fireEvent.change(input, { target: { value: 'Portland' } })
  await screen.findByText(OREGON.label)

  // keep typing and press Enter before the 300 ms debounce runs the new search
  fireEvent.change(input, { target: { value: 'Portland, Maine' } })
  expect(screen.queryByText(OREGON.label)).toBeNull() // the old list is hidden...
  fireEvent.keyDown(input, { key: 'Enter' })
  expect(onPick).not.toHaveBeenCalled() // ...so Enter must not pick from it

  // once the new results show, Enter picks the right place
  await screen.findByText(MAINE.label)
  fireEvent.keyDown(input, { key: 'Enter' })
  expect(onPick).toHaveBeenCalledExactlyOnceWith(MAINE)
})
