# Open-Meteo

Weather forecasts, history since 1940, air quality, and city geocoding.

| | |
|---|---|
| Docs | [open-meteo.com/en/docs](https://open-meteo.com/en/docs) |
| Auth | None |
| Rate limit | 10,000 calls/day, 5,000/hour, 600/minute, per IP. Big requests count as more (see Gotchas). |
| Format | JSON |

## Endpoints

| Purpose | URL |
|---|---|
| Forecast (up to 16 days) | `GET https://api.open-meteo.com/v1/forecast` |
| History (1940 to today) | `GET https://archive-api.open-meteo.com/v1/archive` |
| Air quality | `GET https://air-quality-api.open-meteo.com/v1/air-quality` |
| City → coordinates | `GET https://geocoding-api.open-meteo.com/v1/search` |
| Marine (waves) | `GET https://marine-api.open-meteo.com/v1/marine` |
| Elevation | `GET https://api.open-meteo.com/v1/elevation` |

| Param | Example | Notes |
|---|---|---|
| `latitude`, `longitude` | `41.88`, `-87.63` | Required. Comma lists return an array of locations |
| `daily` | `temperature_2m_max,temperature_2m_min` | Daily variables |
| `hourly` | `temperature_2m,precipitation` | Hourly variables |
| `current` | `temperature_2m,weather_code` | Forecast only |
| `timezone` | `auto` | Default `GMT`. Set it, or days are UTC days |
| `forecast_days`, `past_days` | `7`, `3` | Forecast only |
| `start_date`, `end_date` | `2024-01-01` | Required for history |
| `temperature_unit` | `fahrenheit` | Default celsius |
| `wind_speed_unit` | `mph` | Default `kmh` |
| `precipitation_unit` | `inch` | Default `mm` |

**Geocoding params:** `name` (required), `count` (default 10), `countryCode` (e.g. `US`).

**Useful variables**

| Type | Variables |
|---|---|
| Daily | `temperature_2m_max`, `temperature_2m_min`, `temperature_2m_mean`, `precipitation_sum`, `precipitation_probability_max`, `wind_speed_10m_max`, `uv_index_max`, `sunrise`, `sunset`, `weather_code` |
| Hourly | `temperature_2m`, `apparent_temperature`, `relative_humidity_2m`, `precipitation`, `precipitation_probability`, `cloud_cover`, `wind_speed_10m`, `weather_code` |
| Air quality | `pm2_5`, `pm10`, `ozone`, `nitrogen_dioxide`, `us_aqi`, `european_aqi` |

## Examples

```bash
curl "https://geocoding-api.open-meteo.com/v1/search?name=Chicago&count=1"
curl "https://api.open-meteo.com/v1/forecast?latitude=41.88&longitude=-87.63&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
curl "https://archive-api.open-meteo.com/v1/archive?latitude=41.88&longitude=-87.63&start_date=2024-01-01&end_date=2024-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
```

## Response

Values are **parallel arrays**: `time[i]` matches `temperature_2m_max[i]`.

```json
{
  "latitude": 41.879498,
  "longitude": -87.64974,
  "timezone": "America/Chicago",
  "current": { "time": "2026-09-29T15:30", "interval": 900, "temperature_2m": 22.3, "weather_code": 2 },
  "daily_units": { "temperature_2m_max": "°C", "precipitation_sum": "mm" },
  "daily": {
    "time": ["2026-09-29", "2026-09-30"],
    "temperature_2m_max": [23.4, 19.7],
    "temperature_2m_min": [11.6, 14.6],
    "precipitation_sum": [0.0, 18.1]
  }
}
```

Geocoding:

```json
{
  "results": [
    { "id": 4887398, "name": "Chicago", "latitude": 41.85003, "longitude": -87.65005,
      "country": "United States", "country_code": "US", "admin1": "Illinois",
      "timezone": "America/Chicago", "population": 2664452 }
  ]
}
```

## Sample data

Chicago 7-day forecast, °F, fetched 29 Sep 2026:

| Day | Low | High |
|---|---:|---:|
| Tue Sep 29 | 52.8 | 74.2 |
| Wed Sep 30 | 58.3 | 67.5 |
| Thu Oct 1 | 61.9 | 70.0 |
| Fri Oct 2 | 57.2 | 61.9 |
| Sat Oct 3 | 54.5 | 65.1 |
| Sun Oct 4 | 55.2 | 65.7 |
| Mon Oct 5 | 52.0 | 57.8 |

## Weather codes

| Code | Meaning |
|---|---|
| 0 | Clear |
| 1–3 | Mainly clear to overcast |
| 45, 48 | Fog |
| 51–57 | Drizzle |
| 61–67 | Rain |
| 71–77 | Snow |
| 80–82 | Showers |
| 85–86 | Snow showers |
| 95–99 | Thunderstorm |

## Gotchas

- **Big requests cost more.** Over 2 weeks of data or over 10 variables counts as several calls.
  1 year ≈ 26 calls. 30 years ≈ 780 calls. Cache history; it never changes.
- Limits are per IP. On shared networks (office, VPN) you may get 429s you didn't cause.
- Convert parallel arrays into row objects before sending to the frontend.
- No match in geocoding returns **no `results` key**.
- Ambiguous names: `Paris` returns France first. Use `countryCode=US` for Paris, Texas.
- Errors: HTTP 400 with `{"error": true, "reason": "..."}`. Over the limit: HTTP 429.
- The latest days in history are estimates and may be revised.
- Read units from the response. `mph` comes back as `"mp/h"`.
- Values can be `null`.

## Dashboard ideas

### 1. City comparison
- **Shows:** 2–4 cities side by side: weekly high, low, rain, and a "best day" for each.
- **Endpoint:** `GET /api/weather/compare?cities=Chicago,Austin,Seattle`
- **Backend:** geocode each city, fetch forecasts in one call, reshape arrays, compute stats, score days with your own rule.

### 2. Is this week unusual?
- **Shows:** this week's forecast against the normal range for those dates.
- **Endpoint:** `GET /api/weather/anomaly?city=Denver&years=10`
- **Backend:** fetch the same dates for past years, average them, subtract from the forecast, flag big gaps.
- **Tip:** ten one-week requests cost ~10 calls. One 10-year range costs ~260.

### 3. Outdoor planner
- **Shows:** best 2-hour windows in the next 3 days, based on weather and air quality.
- **Endpoint:** `GET /api/outdoor/windows?city=Los+Angeles`
- **Backend:** join forecast and air-quality data by hour, map AQI to EPA categories, score hours, find the best windows.

### 4. Climate profile
- **Shows:** monthly average temperature and rain, warmest and wettest months, warming trend.
- **Endpoint:** `GET /api/climate/profile?city=Berlin&from=1995&to=2024`
- **Backend:** fetch 30 years of history (~780 calls, so cache it), group by month and year, fit a trend line.
