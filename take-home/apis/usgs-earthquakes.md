# USGS Earthquakes

Near-real-time and historical earthquake data from the U.S. Geological Survey, covering the whole world.

- **Official docs:** https://earthquake.usgs.gov/fdsnws/event/1/ (query API) and
  https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php (summary feeds)
- **Auth:** none
- **Rate limits:** none published. Be reasonable and cache (feeds update about every minute).
- **Format:** GeoJSON (also CSV, KML, QuakeML)

## Endpoints

### 1. Summary feeds (prebuilt, fast, cached by USGS)

`GET https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{level}_{period}.geojson`

| `level` | `period` |
|---------|----------|
| `significant`, `4.5`, `2.5`, `1.0`, `all` | `hour`, `day`, `week`, `month` |

Example: `.../summary/4.5_week.geojson` returns every M4.5+ quake in the past 7 days.

### 2. Query API (flexible filters, any date range)

| Route | Returns |
|-------|---------|
| `GET https://earthquake.usgs.gov/fdsnws/event/1/query` | Matching events |
| `GET https://earthquake.usgs.gov/fdsnws/event/1/count` | Just the count (`format=geojson` gives `{"count": N, "maxAllowed": 20000}`) |

Query parameters:

| Param | Example | Notes |
|-------|---------|-------|
| `format` | `geojson` | Always set this |
| `starttime`, `endtime` | `2026-01-01`, `2026-02-01T12:00:00` | ISO 8601 UTC. Default: last 30 days. |
| `minmagnitude`, `maxmagnitude` | `4.5` | |
| `mindepth`, `maxdepth` | `0`, `70` | km |
| `latitude`, `longitude`, `maxradiuskm` | `37.77`, `-122.42`, `300` | Circle search |
| `minlatitude`, `maxlatitude`, `minlongitude`, `maxlongitude` | | Rectangle search |
| `orderby` | `time`, `time-asc`, `magnitude`, `magnitude-asc` | Default `time` (newest first) |
| `limit`, `offset` | `100`, `1` | Offset is **1-based**. Max 20,000 results per query. |
| `alertlevel` | `green`, `yellow`, `orange`, `red` | PAGER impact alert |
| `eventid` | `us7000abcd` | One event (returns a single Feature, not a collection) |

## Example requests

```bash
curl "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

curl "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson\
&starttime=2026-01-01&minmagnitude=6&orderby=magnitude"

curl "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson\
&latitude=35.68&longitude=139.69&maxradiuskm=300&minmagnitude=3"
```

## Response shape (trimmed)

```json
{
  "type": "FeatureCollection",
  "metadata": { "generated": 1790714399000, "title": "USGS Magnitude 4.5+ Earthquakes, Past Week", "status": 200, "count": 125 },
  "bbox": [-179.9919, -60.2661, 10, 179.6666, 82.6385, 602.188],
  "features": [
    {
      "type": "Feature",
      "id": "us6000tycv",
      "properties": {
        "mag": 4.8,
        "magType": "mb",
        "place": "44 km NNE of Fangale’ounga, Tonga",
        "time": 1790698376037,
        "updated": 1790702124040,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us6000tycv",
        "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/us6000tycv.geojson",
        "felt": null,
        "alert": null,
        "status": "reviewed",
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

## Gotchas

- `geometry.coordinates` is **`[longitude, latitude, depth_km]`**, which is the reverse of the usual lat/lon order.
- `time` and `updated` are **Unix epoch milliseconds** (UTC).
- `mag`, `felt`, `alert` and others may be `null`. `alert` is `null` for the vast majority of events.
- `/query` responses have **no `metadata.count`** (only the summary feeds do). Use `features.length`.
  Pagination uses `limit` and a 1-based `offset`.
- `place` is free text. There's no country field. Parse the text after the last comma
  as a rough region, or reverse-geocode the coordinates. US places use **state abbreviations**
  (`"10 km WNW of The Geysers, CA"`), but Alaska and non-US places use full names
  (`"69 km WNW of Tyonek, Alaska"`), so normalize before grouping.
- `properties.type` isn't always `earthquake`. In a sample month, about 2% of events were `quarry blast`,
  `explosion`, `ice quake`, `mining explosion`, or `landslide`.
- The `all_month` feed is large (about 10,000 events, several MB). Prefer `2.5_` or `4.5_` feeds
  unless you need small quakes.
- Queries matching more than 20,000 events fail with HTTP 400 and a **plain-text** (not JSON) body:
  `"964250 matching events exceeds search limit of 20000..."`. Narrow the range or use `/count` first.
- Prefer the summary feeds for "recent" dashboards, since they're pre-generated and very fast.

## Dashboard ideas

Pick one of these, or combine parts of them. In each idea, the backend does real work:
it aggregates, does geo math, and reshapes GeoJSON into what the UI needs. Just
forwarding the USGS feed doesn't count.

### 1. Global activity overview
**Dashboard shows:** KPI tiles (total quakes, strongest, average depth, # with tsunami flag), a bar
chart of quakes per day, a magnitude histogram, and a table of the 10 strongest.

**Example endpoint:** `GET /api/quakes/summary?period=week&min_mag=2.5`

**Backend work:**
- Pick the right summary feed (or query) for the requested period.
- Bucket by day (handle the time zone) and by magnitude band (<2, 2–4, 4–6, 6+).
- Compute the KPIs, sort, and return a compact shape (not raw GeoJSON features).
- Drop non-earthquake event types and handle `null` magnitudes.

### 2. Earthquakes near a place
**Dashboard shows:** A location picker (a preset city list, or a city search that uses the Open-Meteo
geocoding API) and a radius selector. The result is a table of nearby quakes
sorted by distance, a "distance ring" chart (0–100, 100–250, 250–500 km), and optionally a map.

**Example endpoint:** `GET /api/quakes/nearby?lat=35.68&lon=139.69&radius_km=500&days=30`

**Backend work:**
- Query the USGS API with the radius filter, **then compute the haversine distance** for every
  event yourself (USGS doesn't return it).
- Remember that coordinates are `[lon, lat, depth]`.
- Bucket results into distance rings and find the nearest and strongest events.

### 3. Hotspot leaderboard
**Dashboard shows:** A ranked bar chart of the most active regions, by event count and by total
energy released, for a chosen period.

**Example endpoint:** `GET /api/quakes/hotspots?days=30&group_by=region|grid`

**Backend work:**
- Group events either by region parsed from `place` (the text after the last comma), or by a lat/lon
  grid cell (e.g. 5° × 5°).
- Compute relative energy per event (energy grows ~32× per magnitude step, so ∝ 10^(1.5·M)),
  sum it per group, and rank. Note in your docs that the parsing is imperfect.

### 4. Aftershock tracker
**Dashboard shows:** Pick a recent significant quake and see a time series of aftershocks per
hour or day after the main shock, plus the largest aftershock and the magnitude gap to the main shock.

**Example endpoint:** `GET /api/quakes/{eventId}/aftershocks?radius_km=100&days=14`

**Backend work:**
- Fetch the main event by `eventid`, then run a second query in the window around it (by time and radius).
- Exclude the main shock, bucket the rest by elapsed time, and compute the decay stats.
