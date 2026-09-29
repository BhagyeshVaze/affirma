# CityBikes: Bike-Share Networks

A single, normalized API over 700+ bike-share systems worldwide, with live station
status (bikes available and empty docks).

- **Official docs:** https://api.citybik.es/v2/ and https://docs.citybik.es/api/v2
- **Auth:** none
- **Rate limits:** fair use. Station data refreshes every few minutes, so cache for ~60 s or more.
- **Format:** JSON

Base URL: `https://api.citybik.es/v2`

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /networks` | Every network (id, name, company, city, country, coordinates) |
| `GET /networks/{network_id}` | One network including **all its stations** with live status |

Both accept `?fields=` to limit the returned keys, e.g. `?fields=id,name,location` or `?fields=stations`.

Some common `network_id`s: `citi-bike-nyc`, `divvy` (Chicago), `bay-wheels` (San Francisco),
`capital-bikeshare` (Washington, DC), `velib` (Paris), `santander-cycles` (London),
`bicing` (Barcelona). Use `/networks` to find others. Search by `location.city`.

## Example requests

```bash
curl "https://api.citybik.es/v2/networks?fields=id,name,location"
curl "https://api.citybik.es/v2/networks/citi-bike-nyc"
curl "https://api.citybik.es/v2/networks/divvy?fields=stations"
```

## Response shapes (trimmed)

`/networks`:

```json
{
  "networks": [
    { "id": "citi-bike-nyc", "name": "Citi Bike", "company": ["Lyft"],
      "href": "/v2/networks/citi-bike-nyc",
      "location": { "city": "New York, NY", "country": "US", "latitude": 40.7143, "longitude": -74.006 } }
  ]
}
```

`/networks/{id}`:

```json
{
  "network": {
    "id": "citi-bike-nyc", "name": "Citi Bike",
    "location": { "city": "New York, NY", "country": "US", "latitude": 40.7143, "longitude": -74.006 },
    "stations": [
      { "id": "a1b2c3...", "name": "W 52 St & 11 Ave",
        "latitude": 40.767, "longitude": -73.994,
        "free_bikes": 7, "empty_slots": 32,
        "timestamp": "2026-09-29T14:02:11.123456Z",
        "extra": { "uid": "72", "renting": 1, "returning": 1, "ebikes": 2, "slots": 39 } }
    ]
  }
}
```

## Gotchas

- `empty_slots` can be **`null`** for dockless or "virtual" stations. Handle it before
  computing % full.
- The keys inside `extra` **vary by network**. Don't rely on them unless you check for them.
- Large networks (NYC, Paris) return 1,000–2,000+ stations and a big payload. Summarize on the
  backend and send only what the UI needs.
- Station `id` is a hash that CityBikes generates. `extra.uid` is often the operator's own ID.
- Distance math: use the haversine formula on `latitude`/`longitude`.
