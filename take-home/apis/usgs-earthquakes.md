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
  "metadata": { "generated": 1790000000000, "title": "USGS Magnitude 4.5+ Earthquakes, Past Week", "count": 104 },
  "features": [
    {
      "type": "Feature",
      "id": "us7000abcd",
      "properties": {
        "mag": 5.4,
        "magType": "mww",
        "place": "45 km SSW of Somewhere, Chile",
        "time": 1789912345678,
        "updated": 1789915555555,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000abcd",
        "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/us7000abcd.geojson",
        "felt": 12,
        "alert": "green",
        "tsunami": 0,
        "sig": 449,
        "type": "earthquake",
        "title": "M 5.4 - 45 km SSW of Somewhere, Chile"
      },
      "geometry": { "type": "Point", "coordinates": [-71.23, -33.45, 10.0] }
    }
  ]
}
```

## Gotchas

- `geometry.coordinates` is **`[longitude, latitude, depth_km]`**, which is the reverse of the usual lat/lon order.
- `time` and `updated` are **Unix epoch milliseconds** (UTC).
- `mag`, `felt`, `alert` and others may be `null`.
- `place` is free text. There's no country field. Parse the text after the last comma
  as a rough region, or reverse-geocode the coordinates.
- `properties.type` isn't always `earthquake`. It can also be `quarry blast`, `explosion`, and so on.
- Queries returning more than 20,000 events fail with HTTP 400. Narrow the range or use `/count` first.
- Prefer the summary feeds for "recent" dashboards, since they're pre-generated and very fast.
