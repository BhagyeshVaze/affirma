# National Weather Service (api.weather.gov): US Forecasts & Alerts

Official US government weather data: forecasts, hourly forecasts, active alerts (storms,
floods, heat, and more), and station observations. **US locations only.**

- **Official docs:** https://www.weather.gov/documentation/services-web-api and
  https://weather-gov.github.io/api/general-faqs
- **Auth:** no key, but a **`User-Agent` header is required**, e.g.
  `User-Agent: MyTakeHome/1.0 (you@example.com)`. Requests without one are rejected.
- **Rate limits:** not published but generous. Rapid bursts from one IP can get a temporary block. Cache.
- **Format:** GeoJSON by default (`application/geo+json`)

Base URL: `https://api.weather.gov`

## How forecasts work (two-step lookup)

1. `GET /points/{lat},{lon}` returns the NWS office (`gridId`), grid `gridX`/`gridY`, and **ready-made URLs**
   for that location's forecasts.
2. Follow `properties.forecast` or `properties.forecastHourly` from step 1.

Cache step 1 per location, because it never changes for a given point.

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /points/{lat},{lon}` | Metadata and forecast URLs for a point (max 4 decimal places) |
| `GET /gridpoints/{wfo}/{x},{y}/forecast` | 12-hour periods for ~7 days ("Tonight", "Tuesday", ...) |
| `GET /gridpoints/{wfo}/{x},{y}/forecast/hourly` | Hourly forecast for ~7 days |
| `GET /gridpoints/{wfo}/{x},{y}` | Raw grid data (many variables, as time series) |
| `GET /alerts/active` | All active alerts. Filters: `area=CA`, `point=lat,lon`, `zone=`, `severity=`, `event=` |
| `GET /alerts/active/count` | Counts of active alerts by area, region, and zone |
| `GET /alerts?start=..&end=..` | Past alerts (last ~7 days) |
| `GET /stations/{stationId}/observations/latest` | Latest observation at a station (e.g. `KORD`) |
| `GET /points/{lat},{lon}/stations` | Nearby observation stations *(also linked from `/points`)* |

## Example requests

```bash
UA="MyTakeHome/1.0 (you@example.com)"
curl -A "$UA" "https://api.weather.gov/points/39.7392,-104.9903"
curl -A "$UA" "https://api.weather.gov/gridpoints/BOU/63,62/forecast"
curl -A "$UA" "https://api.weather.gov/alerts/active?area=TX"
curl -A "$UA" "https://api.weather.gov/stations/KORD/observations/latest"
```

## Response shapes (trimmed)

`/points/{lat},{lon}`:

```json
{ "properties": {
    "gridId": "BOU", "gridX": 63, "gridY": 62,
    "forecast": "https://api.weather.gov/gridpoints/BOU/63,62/forecast",
    "forecastHourly": "https://api.weather.gov/gridpoints/BOU/63,62/forecast/hourly",
    "observationStations": "https://api.weather.gov/gridpoints/BOU/63,62/stations",
    "timeZone": "America/Denver",
    "relativeLocation": { "properties": { "city": "Denver", "state": "CO" } } } }
```

`.../forecast`:

```json
{ "properties": { "updated": "2026-09-29T15:00:00+00:00",
    "periods": [
      { "number": 1, "name": "This Afternoon", "startTime": "2026-09-29T12:00:00-06:00",
        "endTime": "2026-09-29T18:00:00-06:00", "isDaytime": true,
        "temperature": 74, "temperatureUnit": "F",
        "probabilityOfPrecipitation": { "unitCode": "wmoUnit:percent", "value": 20 },
        "windSpeed": "5 to 10 mph", "windDirection": "NW",
        "shortForecast": "Partly Sunny", "detailedForecast": "Partly sunny, with a high near 74..." }
    ] } }
```

`/alerts/active`:

```json
{ "features": [
    { "properties": {
        "id": "urn:oid:2.49.0.1.840.0....", "event": "Heat Advisory",
        "areaDesc": "Maricopa, AZ", "severity": "Moderate", "certainty": "Likely", "urgency": "Expected",
        "headline": "Heat Advisory issued ...", "description": "...", "instruction": "...",
        "effective": "2026-09-29T10:00:00-07:00", "expires": "2026-09-30T20:00:00-07:00",
        "senderName": "NWS Phoenix AZ" } }
] }
```

`severity` is one of `Extreme`, `Severe`, `Moderate`, `Minor`, `Unknown`.

## Gotchas

- **US only.** `/points` outside the US returns 404.
- **Forgetting the `User-Agent`** is the most common error. Browsers can't set it, which is one more
  reason to call this from your backend.
- `windSpeed` is a **string** (`"5 to 10 mph"`), so you'll need to parse it if you want numbers.
- Observation values use `{ "unitCode": "wmoUnit:degC", "value": 21.1 }`, where `value` may be `null`.
- The service occasionally returns transient **500/503** errors. Retry once with a short delay, then
  show a friendly error.
- `alerts/active?area=` takes 2-letter state or marine area codes.
