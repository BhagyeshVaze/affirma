const DAY_FMT = new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'numeric', day: 'numeric', timeZone: 'UTC' })
const LONG_FMT = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

// Dates arrive as "YYYY-MM-DD" in the city's local time. Parse as UTC so the browser's
// own timezone can't shift them by a day.
const asDate = (iso) => new Date(`${iso}T00:00:00Z`)

export const dayLabel = (iso) => DAY_FMT.format(asDate(iso)).replace(',', '')
export const shortDate = (iso) => LONG_FMT.format(asDate(iso))

export function num(value, digits = 1) {
  return value == null ? 'n/a' : value.toFixed(digits)
}

export function signed(value, digits = 1) {
  if (value == null) return 'n/a'
  const s = value.toFixed(digits)
  return value > 0 ? `+${s}` : s
}

export function ordinal(n) {
  const r = Math.round(n)
  const tail = r % 100 >= 11 && r % 100 <= 13 ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[r % 10] || 'th'
  return `${r}${tail}`
}

export const VERDICT_TEXT = {
  normal: 'normal',
  somewhat_unusual: 'somewhat unusual',
  very_unusual: 'very unusual',
}

const RANK = { normal: 0, somewhat_unusual: 1, very_unusual: 2 }
export const worstVerdict = (a, b) => (RANK[a] >= RANK[b] ? a : b)
