# USGS Earthquakes

Worldwide earthquakes, live and historical, from the U.S. Geological Survey.

| | |
|---|---|
| Docs | [Query API](https://earthquake.usgs.gov/fdsnws/event/1/) · [Feeds](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) |
| Auth | None |
| Rate limit | None published. Feeds update about every minute. |
| Format | GeoJSON |

## Endpoints

**Summary feeds**: prebuilt and fast. Best for recent data.

`GET https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{level}_{period}.geojson`

| `level` | `period` |
|---|---|
| `significant`, `4.5`, `2.5`, `1.0`, `all` | `hour`, `day`, `week`, `month` |

**Query API**: any date range, with filters.

| Route | Returns |
|---|---|
| `GET https://earthquake.usgs.gov/fdsnws/event/1/query` | Matching events |
| `GET https://earthquake.usgs.gov/fdsnws/event/1/count` | `{"count": N, "maxAllowed": 20000}` |

| Param | Example | Notes |
|---|---|---|
| `format` | `geojson` | Always set |
| `starttime`, `endtime` | `2026-01-01` | UTC. Default: last 30 days |
| `minmagnitude`, `maxmagnitude` | `4.5` | |
| `mindepth`, `maxdepth` | `0`, `70` | km |
| `latitude`, `longitude`, `maxradiuskm` | `37.77`, `-122.42`, `300` | Circle search |
| `minlatitude`, `maxlatitude`, `minlongitude`, `maxlongitude` | | Box search |
| `orderby` | `time`, `time-asc`, `magnitude`, `magnitude-asc` | Default `time` |
| `limit`, `offset` | `100`, `1` | `offset` starts at 1. Max 20,000 results |
| `alertlevel` | `green`, `yellow`, `orange`, `red` | Impact alert |
| `eventid` | `us6000tycv` | Returns one Feature |

## Examples

```bash
curl "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
curl "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-01-01&minmagnitude=6&orderby=magnitude"
curl "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude=35.68&longitude=139.69&maxradiuskm=300&minmagnitude=3"
```

## Response

```json
{
  "type": "FeatureCollection",
  "metadata": { "generated": 1790714399000, "title": "USGS Magnitude 4.5+ Earthquakes, Past Week", "count": 125 },
  "features": [
    {
      "type": "Feature",
      "id": "us6000tycv",
      "properties": {
        "mag": 4.8,
        "place": "44 km NNE of Fangale’ounga, Tonga",
        "time": 1790698376037,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us6000tycv",
        "felt": null,
        "alert": null,
        "tsunami": 0,
        "sig": 354,
        "type": "earthquake",
        "title": "M 4.8 - 44 km NNE of Fangale’ounga, Tonga"
      },
      "geometry": { "type": "Point", "coordinates": [-174.1824, -19.3714, 10] }
    }
  ]
}
```

## Sample data

M4.5+ quakes per UTC day, from `4.5_week.geojson` on 29 Sep 2026:

| Day | Events | Note |
|---|---:|---|
| Tue Sep 22 | 3 | Partial day |
| Wed Sep 23 | 14 | |
| Thu Sep 24 | 12 | |
| Fri Sep 25 | 18 | |
| Sat Sep 26 | 28 | |
| Sun Sep 27 | 12 | |
| Mon Sep 28 | 24 | |
| Tue Sep 29 | 15 | Partial day |

## Gotchas

- Coordinates are **`[lon, lat, depth_km]`**, not lat/lon.
- `time` is Unix **milliseconds**, UTC.
- `mag`, `felt`, and `alert` can be `null`. `alert` usually is.
- Feeds are rolling windows. The first and last days are partial (see sample data). Drop or label them.
- `type` isn't always `earthquake`. About 2% are quarry blasts, explosions, and similar. Filter them.
- `place` is free text with no country field. US places use state codes (`CA`); others use full names (`Alaska`, `Tonga`).
- `/query` responses have no `metadata.count`. Use `features.length`.
- Over 20,000 matches returns HTTP 400 with a **plain-text** body, not JSON.
- `all_month` is about 10,000 events. Use `2.5_` or `4.5_` feeds unless you need small quakes.

## Dashboard ideas

### 1. Activity overview
- **Shows:** totals, strongest quake, quakes per day, magnitude histogram, top 10 table.
- **Endpoint:** `GET /api/quakes/summary?period=week&min_mag=2.5`
- **Backend:** pick the feed, filter non-earthquakes, bucket by day and magnitude band, compute totals.

### 2. Quakes near a place
- **Shows:** location and radius picker, nearby quakes sorted by distance, counts by distance band.
- **Endpoint:** `GET /api/quakes/nearby?lat=35.68&lon=139.69&radius_km=500&days=30`
- **Backend:** query by radius, compute haversine distance yourself (USGS doesn't return it), group into bands.
- **Tip:** Open-Meteo's geocoding API can turn a city name into coordinates.

### 3. Hotspots
- **Shows:** most active regions, ranked by count and by energy released.
- **Endpoint:** `GET /api/quakes/hotspots?days=30`
- **Backend:** group by region (text after the last comma in `place`) or by lat/lon grid cell. Energy ∝ 10^(1.5 × magnitude).

### 4. Aftershocks
- **Shows:** aftershocks per hour or day after a chosen major quake, and the largest one.
- **Endpoint:** `GET /api/quakes/{eventId}/aftershocks?radius_km=100&days=14`
- **Backend:** fetch the main event, query around it by time and radius, exclude it, bucket by elapsed time.
