# Open-Meteo: Weather, Climate & Air Quality

Free weather forecasts, historical weather back to 1940, air quality, and geocoding.
Built from national weather services' models (NOAA, ECMWF, DWD, and others).

- **Official docs:** https://open-meteo.com/en/docs (each sub-API has its own page)
- **Auth:** none
- **Rate limits:** ~10,000 calls/day, 5,000/hour, 600/minute (non-commercial use)
- **Format:** JSON (CSV and XLSX available with `format=csv|xlsx`)

## Endpoints

| Purpose | Method & URL |
|---------|--------------|
| Forecast (up to 16 days, plus recent past) | `GET https://api.open-meteo.com/v1/forecast` |
| Historical weather (1940 to ~5 days ago) | `GET https://archive-api.open-meteo.com/v1/archive` |
| Air quality | `GET https://air-quality-api.open-meteo.com/v1/air-quality` |
| Marine (waves) | `GET https://marine-api.open-meteo.com/v1/marine` |
| City name → coordinates | `GET https://geocoding-api.open-meteo.com/v1/search` |
| Elevation | `GET https://api.open-meteo.com/v1/elevation?latitude=..&longitude=..` |

### Common query parameters (forecast / archive / air quality)

| Param | Example | Notes |
|-------|---------|-------|
| `latitude`, `longitude` | `41.88`, `-87.63` | Required. Comma lists fetch several locations in one call (the response becomes an array). |
| `hourly` | `temperature_2m,precipitation` | Comma list of hourly variables |
| `daily` | `temperature_2m_max,temperature_2m_min` | Comma list of daily variables. Needs `timezone`. |
| `current` | `temperature_2m,weather_code` | Current conditions (forecast API) |
| `timezone` | `auto` or `America/Chicago` | `auto` resolves from coordinates |
| `forecast_days` | `7` | 0–16 (forecast only) |
| `past_days` | `3` | Include recent past in a forecast call |
| `start_date`, `end_date` | `2024-01-01` | **Required** for the archive API; `YYYY-MM-DD` |
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
  "latitude": 41.875,
  "longitude": -87.625,
  "timezone": "America/Chicago",
  "current_units": { "temperature_2m": "°C" },
  "current": { "time": "2026-09-29T14:00", "temperature_2m": 18.4, "weather_code": 2 },
  "daily_units": { "temperature_2m_max": "°C", "precipitation_sum": "mm" },
  "daily": {
    "time": ["2026-09-29", "2026-09-30"],
    "temperature_2m_max": [21.3, 19.8],
    "temperature_2m_min": [12.1, 11.4],
    "precipitation_sum": [0.0, 3.2]
  }
}
```

Geocoding:

```json
{
  "results": [
    { "id": 4887398, "name": "Chicago", "latitude": 41.85, "longitude": -87.65,
      "country": "United States", "country_code": "US", "admin1": "Illinois",
      "timezone": "America/Chicago", "population": 2720546 }
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

- The response is columnar. You'll usually "zip" `time[]` with each value array into
  row objects before sending it to the frontend.
- The geocoding response has **no `results` key** when nothing matches. Handle that case.
- Errors come back as HTTP 400 with `{ "error": true, "reason": "..." }`.
- Archive data lags by about 5 days. Use `past_days` on the forecast API for the last few days.
- Values can be `null` for some hours or models.
- Many variables fit in one call. Prefer one wide request over several narrow ones.
