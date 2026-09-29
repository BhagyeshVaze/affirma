# Open-Meteo: Weather, Climate & Air Quality

Free weather forecasts, historical weather back to 1940, air quality, and geocoding.
Built from national weather services' models (NOAA, ECMWF, DWD, and others).

- **Official docs:** https://open-meteo.com/en/docs (each sub-API has its own page)
- **Auth:** none
- **Rate limits:** 10,000 calls/day, 5,000/hour, 600/minute (free tier, non-commercial use).
  **Big requests count as several calls:** more than 10 variables or more than 2 weeks of data
  counts fractionally (4 weeks = 2 calls, 1 year ≈ 26 calls, 30 years ≈ 780 calls). Going over
  returns HTTP 429 with `{"error":true,"reason":"Daily API request limit exceeded..."}`.
- **Format:** JSON (CSV and XLSX available with `format=csv|xlsx`)

## Endpoints

| Purpose | Method & URL |
|---------|--------------|
| Forecast (up to 16 days, plus recent past) | `GET https://api.open-meteo.com/v1/forecast` |
| Historical weather (1940 to today) | `GET https://archive-api.open-meteo.com/v1/archive` |
| Air quality | `GET https://air-quality-api.open-meteo.com/v1/air-quality` |
| Marine (waves) | `GET https://marine-api.open-meteo.com/v1/marine` |
| City name → coordinates | `GET https://geocoding-api.open-meteo.com/v1/search` |
| Elevation | `GET https://api.open-meteo.com/v1/elevation?latitude=..&longitude=..` |

### Common query parameters (forecast / archive / air quality)

| Param | Example | Notes |
|-------|---------|-------|
| `latitude`, `longitude` | `41.88`, `-87.63` | Required. Comma lists fetch several locations in one call (the response becomes an array). |
| `hourly` | `temperature_2m,precipitation` | Comma list of hourly variables |
| `daily` | `temperature_2m_max,temperature_2m_min` | Comma list of daily variables. Set `timezone` too, or days are GMT/UTC days. |
| `current` | `temperature_2m,weather_code` | Current conditions (forecast API) |
| `timezone` | `auto` or `America/Chicago` | Default `GMT`. `auto` resolves from the coordinates. |
| `forecast_days` | `7` | 0–16 (forecast only) |
| `past_days` | `3` | Include recent past in a forecast call |
| `start_date`, `end_date` | `2024-01-01` | **Required** for the archive API; `YYYY-MM-DD` |
| `format` | `csv` | Optional. Default JSON. |
| `temperature_unit` | `fahrenheit` | Default is celsius |
| `wind_speed_unit` | `mph` | Default is `kmh` |
| `precipitation_unit` | `inch` | Default is `mm` |

### Useful variables

- **Daily:** `temperature_2m_max`, `temperature_2m_min`, `temperature_2m_mean`,
  `precipitation_sum`, `rain_sum`, `snowfall_sum`, `precipitation_probability_max`,
  `wind_speed_10m_max`, `uv_index_max`, `sunrise`, `sunset`, `weather_code`
- **Hourly:** `temperature_2m`, `apparent_temperature`, `relative_humidity_2m`,
  `precipitation`, `precipitation_probability`, `cloud_cover`, `wind_speed_10m`, `weather_code`
- **Air quality (hourly/current):** `pm2_5`, `pm10`, `ozone`, `nitrogen_dioxide`, `us_aqi`, `european_aqi`

### Geocoding parameters

`name` (required), `count` (1–100, default 10), `language` (default `en`), `countryCode` (e.g. `US`).

## Example requests

```bash
curl "https://geocoding-api.open-meteo.com/v1/search?name=Chicago&count=1"

curl "https://api.open-meteo.com/v1/forecast?latitude=41.88&longitude=-87.63\
&current=temperature_2m,weather_code\
&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"

curl "https://archive-api.open-meteo.com/v1/archive?latitude=41.88&longitude=-87.63\
&start_date=2024-01-01&end_date=2024-12-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto"
```

## Response shape (trimmed)

Data is **columnar**: `time` is one array, and each variable is a parallel array with the same index.

```json
{
  "latitude": 41.879498,
  "longitude": -87.64974,
  "utc_offset_seconds": -18000,
  "timezone": "America/Chicago",
  "elevation": 265.0,
  "current_units": { "time": "iso8601", "interval": "seconds", "temperature_2m": "°C", "weather_code": "wmo code" },
  "current": { "time": "2026-09-29T15:30", "interval": 900, "temperature_2m": 22.3, "weather_code": 2 },
  "daily_units": { "time": "iso8601", "temperature_2m_max": "°C", "temperature_2m_min": "°C", "precipitation_sum": "mm" },
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
      "elevation": 179.0, "country": "United States", "country_code": "US",
      "admin1": "Illinois", "admin2": "Cook", "timezone": "America/Chicago",
      "population": 2664452, "postcodes": ["60601", "60602", "..."] }
  ]
}
```

## `weather_code` (WMO) cheat sheet

| Code | Meaning |
|------|---------|
| 0 | Clear sky |
| 1, 2, 3 | Mainly clear, partly cloudy, overcast |
| 45, 48 | Fog |
| 51–57 | Drizzle (incl. freezing) |
| 61–67 | Rain (incl. freezing) |
| 71–77 | Snow |
| 80–82 | Rain showers |
| 85–86 | Snow showers |
| 95–99 | Thunderstorm (96/99 with hail) |

## Gotchas

- Limits are **per IP address**. On a shared network (office, VPN, cloud dev box), other people's
  traffic counts against you, and you may see 429s you didn't cause. Cache, and show a friendly error.
- The response is columnar. You'll usually "zip" `time[]` with each value array into
  row objects before sending it to the frontend.
- The geocoding response has **no `results` key** when nothing matches. Handle that case.
- Errors come back as HTTP 400 with `{ "error": true, "reason": "..." }`.
- The archive reaches up to today, but the most recent days are model estimates that can be revised.
- Ambiguous names: `name=Paris` returns Paris, France first. Use `countryCode=US` to get Paris, Texas.
  Show the `admin1` (state or region) so users can tell matches apart.
- `wind_speed_unit=mph` labels the unit `"mp/h"` in `daily_units`. Read units from the response rather than hard-coding them.
- Values can be `null` for some hours or models.
- Many variables fit in one call. Prefer one wide request over several narrow ones, and cache
  archive responses, because history never changes and long ranges are expensive (see rate limits).

## Dashboard ideas

Pick one of these, or combine parts of them. In each idea, the backend does real work: it
joins calls, reshapes the columnar arrays, and computes new values. Just forwarding the
Open-Meteo JSON to the browser doesn't count.

### 1. City weather showdown
**Dashboard shows:** 2–4 cities side by side: a card per city with this week's high, low, and total
rain, a grouped bar chart of daily highs, and a "best day of the week" badge for each city.

**Example endpoint:** `GET /api/weather/compare?cities=Chicago,Austin,Seattle&units=imperial`

**Backend work:**
- Geocode each city name. Handle "not found" and ambiguous matches.
- Fetch forecasts, ideally in **one** multi-location call.
- Convert the columnar `daily` arrays into row objects.
- Compute weekly high, low, mean, and total precipitation, and rank the cities.
- Pick a "best day" with a scoring function you design and document, e.g. temperature near 22 °C,
  low precipitation, and low wind.

### 2. Is this week unusual? (climate anomaly)
**Dashboard shows:** A line chart of the next 7 days' forecast highs over a shaded band of the
"normal" range for those calendar days, plus a bar chart of each day's difference from normal.

**Example endpoint:** `GET /api/weather/anomaly?city=Denver&years=10`

**Backend work:**
- Pull the same calendar days from the **archive API** for the past N years. One short request per
  year costs about 1 call each, while a single 10-year range costs about 260 calls (see rate limits). Weigh the trade-off.
- Group by month and day, then compute the mean, min, and max for each day.
- Join those normals to the forecast by date and compute the anomaly (forecast − normal).
- Flag days more than ±X° from normal.

### 3. Outdoor activity planner (weather + air quality)
**Dashboard shows:** A heatmap of days × hours colored by an "outdoor score", and a list of the best
2-hour windows in the next 3 days, with the EPA AQI category for each.

**Example endpoint:** `GET /api/outdoor/windows?city=Los+Angeles&activity=run`

**Backend work:**
- Call both the **forecast** API (temperature, precipitation probability, wind) and the **air-quality**
  API (`us_aqi`), then join them by timestamp.
- Map AQI to EPA categories (0–50 Good, 51–100 Moderate, 101–150 Unhealthy for Sensitive Groups, ...).
- Score each hour, then find the best consecutive windows.

### 4. Climate profile of a city
**Dashboard shows:** A classic climate chart (monthly average temperature line plus monthly
precipitation bars), the warmest and wettest months, and a year-over-year warming trend.

**Example endpoint:** `GET /api/climate/profile?city=Berlin&from=1995&to=2024`

**Backend work:**
- Fetch 30 years of daily archive data, then aggregate it by month and by year. A 30-year request
  counts as about 780 of your 10,000 daily calls, so **cache it**. Don't re-fetch on every page load.
- Compute each year's annual mean and a linear-regression slope (°C per decade).
