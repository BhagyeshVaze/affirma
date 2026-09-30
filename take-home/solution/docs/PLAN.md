# Plan: "Is this week unusual?" dashboard

v1, 30 Sep 2026. Written before any code. Update this file as decisions change.

Status: the section 2 defaults were adopted to fit the time box. Each one is a named constant in
`backend/app/anomaly.py` or `backend/app/config.py`, so it can be changed in one place.

## 1. Goal

The user picks a city. The dashboard shows the next 7 days of forecast highs and lows against the
normal range for those same dates over the past N years, flags which days are unusual, and shows
how this week ranks against the same week in each past year.

Data source: Open-Meteo (geocoding, forecast, and historical archive APIs). Free, no key.

## 2. Decisions to confirm

Defaults are what the plan below assumes.

| # | Decision | Default | Alternatives |
|---|---|---|---|
| 1 | What "this week" means | Today plus the next 6 days, in the city's local time | Calendar week, Mon to Sun |
| 2 | Baseline length | Last 10 years; user can pick 5 to 30 | 30 years (the standard climate-normal length; 30 calls per new city) |
| 3 | Window around each date | Plus or minus 3 days, so 70 samples per day at 10 years. A 13-day request counts as 1 call | Plus or minus 7 days (2 calls per year) |
| 4 | "Unusual" rule | Outside the 10th to 90th percentile is unusual; outside the 2nd to 98th is very unusual | Fixed degrees (for example 10°F), or z-score of 1 and 2 |
| 5 | Week verdict | Count of unusual days: 0 to 1 normal, 2 to 4 somewhat unusual, 5 to 7 very unusual | Weekly average vs past weeks |
| 6 | Second computed endpoint | Same week in each past year, with a rank | Multi-city "which city is most unusual" |
| 7 | Location input | Search, then pick (sends lat and lon). `city=` also accepted | City name only |
| 8 | Units | °F by default, toggle to °C | |
| 9 | Variables | Daily high, daily low, rain | Add wind or UV |

Why decision 4 matters, from a dry run on real Denver data (section 11): Denver's fall highs vary
a lot, so a day 11.5°F above normal is only at the 89th percentile. The percentile rule calls it
normal; a fixed 10°F rule would call it unusual. Percentiles adjust to each city's own spread.

## 3. Architecture

```
React (Vite, :5173)  --/api proxy-->  FastAPI (:8000)  -->  Open-Meteo
                                          |                  geocoding-api  /v1/search
                                   in-memory cache           api            /v1/forecast
                                                             archive-api    /v1/archive
```

```
solution/
  README.md
  backend/
    app/main.py         FastAPI app, CORS, error handlers
    app/config.py       timeouts, TTLs, limits in one place
    app/routes.py       the three endpoints
    app/openmeteo.py    httpx client: timeouts, retry, 429 handling, cache, in-flight dedup
    app/cache.py        TTL caches
    app/dates.py        year shifting, windows, Feb 29 handling
    app/anomaly.py      pure math (no I/O), easy to test
    app/models.py       Pydantic request and response models
    tests/
    requirements.txt
  frontend/             Vite + React + Recharts
  docs/                 PLAN.md, DECISIONS.md, AI_NOTES.md
```

## 4. Endpoints

All responses are JSON. Temperatures and rain are fetched in metric and converted at the end,
so units never enter a cache key.

### Shared location parameters (both weather endpoints)

| Param | Type | Rules | Default |
|---|---|---|---|
| `city` | string | 2 to 100 characters, trimmed | none |
| `lat` | float | -90 to 90, needs `lon` | none |
| `lon` | float | -180 to 180, needs `lat` | none |
| `years` | int | 5 to 30 | 10 |
| `units` | enum | `imperial` or `metric` | `imperial` |

Send exactly one of: `city`, or both `lat` and `lon`. Anything else returns `invalid_input`.
When `city` is used, the first geocoding match is taken and returned in `location`, so the user
can see which place was picked ("Paris, Île-de-France, France").

---

### 4.1 `GET /api/cities` (search helper for the city picker)

Light transform. Not counted as one of the two computed endpoints.

**Params:** `q` (2 to 100 characters), `count` (1 to 10, default 5).

**Upstream:** `GET geocoding-api.open-meteo.com/v1/search?name={q}&count={count}` (1 call, cached).

**Transform:** a missing `results` key becomes an empty list. Build a display label from name,
`admin1` (can be missing), and country. Drop entries without coordinates.

**Response:**

```json
{
  "query": "Paris",
  "results": [
    { "id": 2988507, "label": "Paris, Île-de-France, France", "name": "Paris",
      "admin1": "Île-de-France", "country": "France", "country_code": "FR",
      "latitude": 48.85341, "longitude": 2.3488, "timezone": "Europe/Paris", "population": 2138551 }
  ]
}
```

**Errors:** `invalid_input` (422), `upstream_*` (see section 5). No match is **200 with an empty
list**, not an error, so the search box can show "No places match".

---

### 4.2 `GET /api/weather/anomaly` (core endpoint)

Example: `/api/weather/anomaly?lat=39.74&lon=-104.98&years=10&units=imperial`

**Upstream calls (cold cache):**

1. Geocoding, only if `city` was sent: `/v1/search?name={city}&count=1`.
2. Forecast, 1 call:
   `/v1/forecast?latitude&longitude&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto&forecast_days=7`
3. Archive, 1 call per past year y = 1..N, same `daily` fields and `timezone=auto`:
   `start_date = shift(first_day, y) - 3 days`, `end_date = shift(last_day, y) + 3 days`.
   That is 13 days, which counts as 1 call.

Cost: about 11 calls at N = 10 on a cold cache, 0 on a warm one. One 10-year range would cost
about 260, which is why we fetch year by year.

**Math.** The week is the 7 dates in the forecast's `daily.time` (the city's local today plus 6).
Never use the server clock.

For each forecast day `d` and each variable `v` in {high, low}:

```
S      = values of v on shift(d, y) + j   for y in 1..N, j in -3..3, skipping nulls
normal = mean(S)
p10, p90 = statistics.quantiles(S, n=10, method="inclusive")[0], [8]
anomaly  = forecast - normal
pct_rank = 100 * (count(s < forecast) + 0.5 * count(s == forecast)) / len(S)
level    = "unknown"       if len(S) < 30 or forecast is null
           "very_unusual"  if pct_rank < 2  or pct_rank > 98
           "unusual"       if pct_rank < 10 or pct_rank > 90
           "normal"        otherwise
direction = "warmer" if anomaly > 0 else "cooler"
```

`shift(d, y)` subtracts y years. If that date doesn't exist (Feb 29 in a non-leap year), it
uses Feb 28.

Week summary:

- `avg_high_anomaly`, `avg_low_anomaly` are the means of the 7 daily anomalies.
- `unusual_days` counts days where the high or the low is unusual or very unusual.
- `verdict` is `normal` for 0 to 1 days, `somewhat_unusual` for 2 to 4, and `very_unusual` for 5 to 7.

Rain is mostly zeros, so there are no daily percentiles for rain. The forecast weekly total is
compared with each past year's total over the exact same 7 dates: `avg_total`, `years_wetter`,
`years_drier`.

Unit conversion happens last. Temperatures use `C * 1.8 + 32`. Anomalies and spreads use
`C * 1.8`, with no `+ 32`. Rain uses `mm / 25.4`.

**Response** (high values are from the Denver dry run; the rest are illustrative):

```json
{
  "location": { "name": null, "latitude": 39.74, "longitude": -104.98, "timezone": "America/Denver" },
  "units": { "temperature": "°F", "precipitation": "in" },
  "baseline": { "years_requested": 10, "years_used": 10, "from_year": 2016, "to_year": 2025,
                "window_days": 3, "samples_per_day": 70 },
  "week": {
    "start": "2026-09-30", "end": "2026-10-06",
    "avg_high_anomaly": 4.9, "avg_low_anomaly": 3.2,
    "unusual_days": 1, "very_unusual_days": 0, "verdict": "normal",
    "rain": { "forecast_total": 0.0, "avg_total": 0.31, "years_wetter": 7, "years_drier": 0 }
  },
  "days": [
    { "date": "2026-10-05",
      "high": { "forecast": 83.7, "normal": 72.2, "p10": 58.6, "p90": 83.8,
                "anomaly": 11.5, "pct_rank": 89, "level": "normal", "direction": "warmer", "n": 70 },
      "low":  { "forecast": 63.1, "normal": 45.0, "p10": 36.0, "p90": 55.0,
                "anomaly": 18.1, "pct_rank": 99, "level": "very_unusual", "direction": "warmer", "n": 70 },
      "rain": { "forecast": 0.0 } }
  ],
  "warnings": [],
  "meta": { "upstream_calls": 11, "generated_at": "2026-09-30T11:00:00Z" }
}
```

**Errors:** `invalid_input` (422), `city_not_found` (404), `upstream_rate_limited` (503),
`upstream_timeout` (504), `upstream_error` (502), `insufficient_history` (502).

---

### 4.3 `GET /api/weather/same-week` (second computed endpoint)

Answers: "How does this week compare with the same week in each past year?"

Example: `/api/weather/same-week?lat=39.74&lon=-104.98&years=10&units=imperial`

**Upstream calls:** the same forecast and archive calls as 4.2, with the same cache keys. It costs
0 extra calls if 4.2 ran first. When the frontend calls both at once, in-flight dedup (section 6)
makes them share one fetch.

**Math:**

- For each y in 1..N, take the exact 7 shifted dates (a subset of the cached window). Compute
  `avg_high`, `avg_low`, `total_rain`, and `days_with_data`.
- Add this year's forecast week as the last entry, with `is_forecast: true`.
- `rank_warmest` ranks by `avg_high` among entries with at least 6 days of data, where 1 is the warmest.
- `vs_past_mean` is this week's `avg_high` minus the mean of the past years' `avg_high`.
- The year label is the year of the shifted start date, since a week can cross Jan 1.
- A trend line is a stretch goal. Show it only when `years >= 20`, always with a 95% CI
  (`scipy.stats.linregress`). With 10 points, a trend is mostly noise.

**Response** (illustrative):

```json
{
  "location": { "name": null, "latitude": 39.74, "longitude": -104.98, "timezone": "America/Denver" },
  "units": { "temperature": "°F", "precipitation": "in" },
  "week": { "start": "2026-09-30", "end": "2026-10-06" },
  "years": [
    { "year": 2016, "start": "2016-09-30", "end": "2016-10-06",
      "avg_high": 70.2, "avg_low": 42.1, "total_rain": 0.12, "days_with_data": 7, "is_forecast": false },
    { "year": 2026, "start": "2026-09-30", "end": "2026-10-06",
      "avg_high": 78.9, "avg_low": 50.3, "total_rain": 0.0, "days_with_data": 7, "is_forecast": true }
  ],
  "this_week": { "rank_warmest": 2, "out_of": 11, "vs_past_mean": 5.1 },
  "trend": null,
  "warnings": [],
  "meta": { "upstream_calls": 0, "generated_at": "2026-09-30T11:00:01Z" }
}
```

**Errors:** same as 4.2.

## 5. Error handling

One error shape for every endpoint, including FastAPI's own validation errors, which are
converted by an exception handler:

```json
{ "error": { "code": "upstream_rate_limited", "message": "Weather service is busy. Try again in 60 s.",
             "retry_after_s": 60 } }
```

| Situation | HTTP | `code` |
|---|---|---|
| Bad or missing params, or `city` and `lat`/`lon` both sent or both missing | 422 | `invalid_input` |
| City name has no geocoding match | 404 | `city_not_found` |
| Open-Meteo returns 429, or our own call budget is used up | 503 + `Retry-After` | `upstream_rate_limited` |
| Open-Meteo times out, even after 1 retry | 504 | `upstream_timeout` |
| Open-Meteo 5xx, empty body, bad JSON, or an unexpected 400 | 502 | `upstream_error` |
| Too few past years came back (fewer than 3, or under 70% of `years`) | 502 | `insufficient_history` |

**Client policy (`openmeteo.py`)**

- Use one shared `httpx.AsyncClient`, with a 3 s connect timeout and an 8 s read timeout.
  Calls took about 0.4 s in testing.
- Retry once after 0.5 s on a timeout, a connection error, a 5xx, or an empty body. Never retry
  a 400 or a 429.
- On a 429, use the `Retry-After` header if present, else 60 s.
- Archive calls run concurrently, 5 at a time at most (`asyncio.Semaphore`).
- The budget guard is a sliding 60-second counter of upstream calls. Above 500 a minute, refuse
  with `upstream_rate_limited` rather than calling (Open-Meteo allows 600 a minute per IP).
- Log upstream `reason` text but never show it to users. Some of it is wrong (see gotcha 5).
- Partial failures: if any archive call gets a 429, the whole request returns 503. Otherwise,
  drop the failed years, add a warning, and report `years_used`. Below the threshold, return
  `insufficient_history`.

## 6. Caching

In memory, using `cachetools.TTLCache` with a max size.

| What | Key | TTL | Why |
|---|---|---|---|
| Geocoding | lowercased, trimmed query + count | 24 h | Place names don't change |
| Forecast | lat, lon rounded to 2 decimals | 30 min | Forecasts update a few times a day |
| Archive window | lat, lon (2 decimals), start, end | 7 days | Past years don't change, and we never fetch the recent days that get revised |

- **Rounding to 2 decimals** (about 1 km) raises the hit rate. The model grid is coarser anyway:
  Open-Meteo snapped Denver to a different point.
- **Per-year keys:** going from 10 to 20 years fetches only the 10 new years.
- **In-flight dedup:** keep a dict of key to pending `asyncio.Task`. The frontend calls both
  weather endpoints at once, and without this, a new city would be fetched twice.
- **Units are not in any key.** We always fetch metric.
- **Run one worker.** Each process has its own cache.
- `meta.upstream_calls` shows the cache working, which is useful for a screenshot and for reviewers.

## 7. React components

```
App                          state: place {label, lat, lon}, years, units
├── Header
├── ControlsBar
│   ├── CitySearch           debounced 300 ms, min 2 chars, GET /api/cities, dropdown, keyboard nav
│   ├── YearsSelect          5 / 10 / 20 / 30
│   └── UnitsToggle          °F / °C
├── EmptyState               before a city is picked: "Search for a city to begin"
└── Dashboard                after a pick; fires both weather requests in parallel
    ├── VerdictBanner        verdict, "N of 7 days unusual", avg anomalies, "vs last 10 years"
    ├── WeekChart            Recharts ComposedChart, with a Highs / Lows toggle
    ├── DayTable             7 rows: date, forecast, normal, anomaly, percentile, LevelBadge
    ├── RainCard             weekly total vs past years
    └── SameWeekChart        bar per year, this week highlighted, "2nd warmest of 11"

shared:  LoadingSkeleton, ErrorState (message + Retry), LevelBadge
lib:     api.js (fetch wrappers, parses our error shape), useApi(url) hook
```

- **WeekChart:** the x-axis shows day labels ("Wed 9/30"). A shaded band covers p10 to p90, a
  dashed line shows normal, and a line with dots shows the forecast. Dots differ by level in
  both shape and color, so color is never the only signal. The tooltip shows forecast, normal,
  anomaly, and percentile.
- **useApi:** returns `{status: idle | loading | success | error, data, error, retry}`. It uses
  `AbortController` to cancel stale requests when the city, years, or units change.
- **Each section has its own states,** so one failed request doesn't blank the page.
  - Loading: skeletons.
  - Empty: no city yet; the search has no matches; a day with null data shows "no data".
  - Error: `city_not_found` shows inline under the search box. 503 shows "Weather service busy,
    try again in N s" with a Retry button. 502 and 504 show a generic message with Retry.
- **Vite dev proxy:** `/api` goes to `http://localhost:8000`. The frontend only talks to our
  backend. CORS is also enabled for `localhost:5173` as a fallback.
- **Footnote on the page:** "Normals come from historical reanalysis for the last N years."
  (See gotchas 2 and 17.)

## 8. Gotchas

**Verified with real requests while planning (30 Sep 2026)**

1. **The archive silently accepts impossible dates.** `start_date=2025-02-29` returned data
   starting 2025-03-01, with no error. Build dates with Python's `date`, which raises on bad
   dates, and map Feb 29 to Feb 28 ourselves.
2. **Forecast and archive snap to different grid points.** For Denver, the forecast used 39.747,
   -104.987 and the archive 39.754, -105.021. The baseline is reanalysis and the forecast is a
   weather model, so there can be a built-in offset, larger in mountains and on coasts. This is a
   known limitation; record it in DECISIONS.md and the page footnote.
3. **Geocoding returns HTTP 200 with no `results` key** for both "no match" and 1-character queries.
4. **An end date before the start date** returns a generic `"Bad Request"`. Validate before calling.
5. **Some upstream error text is wrong.** `forecast_days=17` says "Given 16". Log it, don't show it.
6. **One archive call returned HTTP 200 with an empty body.** The retry worked. Handle empty
   bodies as retryable.
7. **Each call takes about 0.4 s,** so 10 sequential archive calls take about 4 s. Run them concurrently.
8. **The archive accepts dates up to today,** and the latest days are estimates. We only use
   dates at least a year old, so revisions can't affect us.

**From the API doc**

9. Set `timezone=auto` on every call, or days are UTC days. Take the week from the forecast's
   `daily.time`, not the server clock.
10. One 10-year range costs about 260 calls. Ten 13-day windows cost about 10.
11. Data comes as parallel arrays; convert them to rows. Values can be `null`: skip them in
    samples and require `n >= 30`.
12. Names can be ambiguous ("Paris" returns France first). Search, pick, then send lat and lon.
13. Limits are per IP. Shared networks (office, VPN) can cause 429s we didn't trigger.

**From our own design**

14. **Weeks that cross Jan 1:** shift each date by the year offset. Don't set `year = Y`.
15. **Units:** values use `* 1.8 + 32`, but anomalies and spreads use `* 1.8` only.
16. **Rain** is zero-inflated, so compare weekly totals only.
17. **A 10-year baseline is short and recent.** "Unusual" means unusual for the last 10 years,
    not against a 30-year climate normal. Say so on the page.

## 9. Tests (pytest)

- **Dates:** Feb 29 maps to Feb 28; a week crossing Jan 1; a window is exactly 13 days.
- **Math:** `pct_rank` with ties; level thresholds at the boundaries (2, 10, 90, 98); `n < 30`
  gives `unknown`; nulls are skipped; value vs delta unit conversion.
- **Parsing:** parallel arrays become rows; a missing `results` key becomes an empty list.
- **Routes,** with Open-Meteo mocked by `respx`:
  - happy path
  - 429 returns 503 with `Retry-After`
  - timeout returns 504
  - an empty body is retried, then succeeds
  - an unknown city returns 404
  - `lat=95` returns 422
  - 1 of 10 years failing returns 200 with a warning
- **Fixtures:** real Denver responses saved once during development.

## 10. Build order and commits (about 3.5 h)

Small commits, no squashing.

| # | Commit | Time |
|---|---|---|
| 1 | docs: plan (this file) | first, before code |
| 2 | backend skeleton: FastAPI app, `/api/health`, requirements | 10 min |
| 3 | Open-Meteo client: timeouts, retry, 429 mapping, cache, dedup | 35 min |
| 4 | dates + anomaly math + tests | 40 min |
| 5 | routes: cities, anomaly, same-week, error handlers, route tests | 35 min |
| 6 | frontend scaffold: Vite, proxy, `api.js`, `useApi` | 15 min |
| 7 | CitySearch, controls, empty / loading / error states | 30 min |
| 8 | VerdictBanner, WeekChart, DayTable | 35 min |
| 9 | SameWeekChart, RainCard | 15 min |
| 10 | README (under 5 min setup, screenshots), DECISIONS.md, AI_NOTES.md | 20 min |

If time runs short, cut in this order: trend line, RainCard, budget guard, SameWeekChart polish.
Keep the same-week endpoint itself, since it is the second computed endpoint.

## 11. How this plan was made

**Prompt** (to Claude, via Claude Code):

> Plan the "Is this week unusual?" dashboard. For each endpoint give the route, params, upstream
> calls, math, response shape, and errors. Then outline the React components. Flag caching and
> gotchas.

**Inputs:** `take-home/README.md`, `take-home/apis/README.md`, `take-home/apis/open-meteo.md`.

**Checks run before writing:**

- Real requests to geocoding, forecast, and archive, including the error cases. The results are
  gotchas 1 to 8.
- A throwaway script ran the anomaly math on real Denver data (not part of the solution).
  Forecast highs, °F, week of 30 Sep 2026, against a 10-year baseline with a 3-day window
  (70 samples per day):

| Date | Forecast | Normal | p10 | p90 | Anomaly | Percentile |
|---|---:|---:|---:|---:|---:|---:|
| Sep 30 | 71.1 | 75.9 | 62.4 | 87.5 | -4.8 | 28 |
| Oct 1 | 70.3 | 75.6 | 62.4 | 87.1 | -5.3 | 27 |
| Oct 2 | 81.9 | 75.1 | 64.4 | 86.1 | +6.8 | 72 |
| Oct 3 | 81.9 | 73.0 | 62.0 | 85.0 | +8.8 | 76 |
| Oct 4 | 81.5 | 72.2 | 58.6 | 83.8 | +9.3 | 79 |
| Oct 5 | 83.7 | 72.2 | 58.6 | 83.8 | +11.5 | 89 |
| Oct 6 | 79.2 | 71.4 | 58.0 | 83.2 | +7.7 | 71 |

The method gives sensible numbers. No high this week falls outside the 10th to 90th percentile,
even at 11.5°F above normal, because Denver's p10 to p90 spread is about 25°F. That is the
evidence behind decision 4.

**What to review in this plan:** the decisions in section 2. Record any AI mistakes found during
the build in `docs/AI_NOTES.md`.
