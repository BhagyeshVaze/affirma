# Is this week unusual?

A dashboard that compares the next 7 days of forecast weather for a city with the same dates in
past years, and says which days are unusual.

- **Backend:** Python, FastAPI, httpx. It calls Open-Meteo (geocoding, forecast, and historical
  archive) and computes the comparison itself.
- **Frontend:** React, Vite, and Recharts. It calls only our backend.

![Dashboard for Denver](docs/screenshots/dashboard.png)

## Run it (about 3 minutes)

Needs Python 3.11+ and Node 20.19+ or 22.12+ (Vite 7 needs one of these). No API keys.

**1. Backend** (terminal 1)

```bash
cd take-home/solution/backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

**2. Frontend** (terminal 2)

```bash
cd take-home/solution/frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Pick a city, or click one of the example cities.

**Tests.** Backend (from `backend/`, with the virtual env active):

```bash
python -m pytest
```

Frontend (from `frontend/`):

```bash
npm test
```

There are 84 backend tests. They cover the math, dates, units, parsing, odd upstream replies,
caching, the call budget, and every route, with Open-Meteo mocked, so they need no network.
There are 2 frontend tests, for the city search's keyboard and debounce behavior.

## What the dashboard shows

- **Verdict:** two separate verdicts, for example "Days: normal. Nights: very unusual." Each
  shows how many of the 7 days fall outside the normal range, and the average difference from
  normal.
- **Week chart:** the forecast against a shaded normal range (5th to 95th percentile of past
  values) and the average. Days that are unusually warm or cool are marked. Toggle highs or lows.
- **Same week in past years:** the average high for these 7 dates in each past year, with this
  week highlighted and ranked.
- **Rain:** this week's forecast total against the same 7 dates in past years.
- **Day-by-day table:** forecast, normal, difference, percentile, and a level for every day.
- **Controls:** city search, baseline length (5, 10, 20, or 30 years), °F or °C, highs or lows.
  The picked city is kept in the URL, so a view can be shared.
- **States:** loading skeletons, an empty state with example cities, "no places match" in the
  search, and error messages with a retry button.

| Empty state | Error state (bad input) |
|---|---|
| ![Empty state](docs/screenshots/empty-state.png) | ![Error state](docs/screenshots/error-state.png) |

## How "unusual" is worked out

For each forecast day, the baseline is every value on the same calendar date, plus or minus 3
days, in each past year. At 10 years that is 70 values per day.

- **Day level:** the forecast's percentile rank among those values.
  - Between the 5th and 95th percentile is **normal**.
  - Outside that range is **unusual**.
  - Outside the 2nd to 98th percentile is **very unusual**.
- **Week verdict:** days (highs) and nights (lows) are judged separately and never combined.
  For each, 0 to 2 flagged days is **normal**, 3 to 4 **somewhat unusual**, and 5 to 7
  **very unusual**. If fewer than 5 days have enough past data to judge, it is
  **not enough history**.
- **Rain:** compared as weekly totals, because daily rain is mostly zeros.

**How the rule was picked:** we wanted "unusual" to be rare, so the rule was backtested on 357
real past weeks in 7 cities (`scripts/backtest_verdict.py`). The first version called 75% of
ordinary weeks unusual. The current rule calls about 83% of weeks normal and about 3% very
unusual, for both highs and lows, in 2025 and 2024. The full table of 10 candidate rules is in
[docs/DECISIONS.md](docs/DECISIONS.md).

To rerun the backtest (from `backend/`, with the virtual env active):

```bash
python ../scripts/backtest_verdict.py
```

The first run downloads about 2,200 calls' worth of history and takes about 5 minutes. After
that it runs from a local cache in 2 seconds.

## Limitations

- **The baseline doesn't account for warming.** It is the last N years as they were, so in a
  warming climate, recent weeks are flagged warm more often than cool.
- **Forecast uncertainty is ignored.** Day 7 is treated as if it were as reliable as day 1.
- **The live app may flag differently than the backtest.** The forecast and the history come
  from different models, and the backtest compares history with history. Forecasts smooth out
  further ahead, which means fewer flags. The gap between the two sources (within about 2°F on
  average, up to about 4°F on single days) adds noise, which means more flags. We don't know
  which effect wins.
- **The cache is in memory,** so it is lost on restart.
- **Too little history gives no verdict.** If fewer than 5 of the 7 days have enough past data
  (for example, 5 years with one year failing to load), the banner says "not enough history"
  instead of guessing.

## Known issues

Small problems found in review and left as they are. None of them change a verdict in normal use.

- **A week with Feb 29 counts Feb 28 twice** in past years that have no Feb 29. This affects the
  same-week averages and rain totals slightly. It next matters in 2028.
- **A dot right at the edge of the shaded band can look wrong.** The band edges are smoothed
  values, while a day is flagged by its rank. So a dot can sit just outside the band and still be
  "normal", or the other way round. The table's level is the one that counts.
- **"Upstream calls" can say 0 on a first load.** When both weather requests start together, they
  share one fetch, and only the request that started it reports the calls. The other says 0.
- **The city search is only partly screen-reader friendly.** Arrow keys move the highlight, but
  the highlighted option isn't announced to screen readers.
- **A small layout slip on phones.** In the same-week chart legend, the blue swatch can wrap onto a
  different line from its "This week (forecast)" label.
- **A crash (500) response has no CORS header.** This doesn't matter through the dev proxy the
  README uses; it would only matter if the frontend were served from a different origin.

## API

Interactive docs: <http://localhost:8000/docs>.

| Route | What it does |
|---|---|
| `GET /api/cities?q=Paris&count=5` | City search, cleaned up. No match returns an empty list. |
| `GET /api/weather/anomaly?lat=39.74&lon=-104.98&years=10&units=imperial` | This week vs the normal range, per day and overall |
| `GET /api/weather/same-week?lat=39.74&lon=-104.98&years=10&units=imperial` | This week vs the same week in each past year, with a rank |

Both weather routes also accept `city=Denver` instead of `lat` and `lon`.

Errors always look like this:

```json
{ "error": { "code": "upstream_rate_limited", "message": "...", "retry_after_s": 60 } }
```

| Status | `code` | When |
|---|---|---|
| 422 | `invalid_input` | Bad or missing parameters |
| 404 | `city_not_found` | The city name has no match |
| 503 | `upstream_rate_limited` | Open-Meteo returned 429, or our own call budget is used up. Sends `Retry-After`. |
| 504 | `upstream_timeout` | Open-Meteo timed out, even after one retry |
| 502 | `upstream_error` / `insufficient_history` | Open-Meteo failed, or too few past years loaded |

## Caching and rate limits

- Everything is cached in memory:
  - geocoding for 24 h
  - forecasts for 30 min
  - past-year history for 7 days (it doesn't change)
- History is fetched as one 13-day window per year, which costs about 1 call each. One 10-year
  range would cost about 260.
- A new city at 10 years costs 11 upstream calls and takes under a second. A repeat costs 0.
  `meta.upstream_calls` in each response shows the count.
- Identical requests made at the same moment share one upstream fetch, so the two weather routes
  loading a new city together don't double the calls.
- A sliding 60-second budget refuses calls above 500 a minute, which keeps us under Open-Meteo's
  limit of 600 a minute.

## Project layout

```
backend/
  app/main.py        app, CORS, error handlers
  app/routes.py      the three routes
  app/openmeteo.py   upstream client: timeouts, retry, 429 handling, caching
  app/anomaly.py     the math (pure functions)
  app/dates.py       year shifting, Feb 29
  app/units.py       °C/°F, mm/in
  app/cache.py       TTL cache with in-flight dedup, call budget
  app/models.py      response models
  tests/
scripts/
  backtest_verdict.py  scores verdict rules on real past weeks
frontend/src/
  App.jsx            layout, controls, state
  useApi.js, api.js  fetching, abort, error shape
  components/        CitySearch, WeekChart, SameWeekChart, DayTable, VerdictBanner, RainCard, ...
docs/
  PLAN.md            the plan, written before code
  DECISIONS.md       trade-offs, known limits, next steps
  AI_NOTES.md        how AI was used, key prompts, and what it got wrong
```
