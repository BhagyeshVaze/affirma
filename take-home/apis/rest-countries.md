# REST Countries

Reference data for about 250 countries: names, ISO codes, capitals, region, population, area,
currencies, languages, borders, flags, time zones, and more.

- **Official docs:** https://restcountries.com/ (source: https://gitlab.com/restcountries/restcountries)
- **Auth:** none
- **Rate limits:** none published. The data is nearly static, so cache it for a day or more.
- **Format:** JSON

Base URL: `https://restcountries.com/v3.1`

## Endpoints

| Route | Example |
|-------|---------|
| `GET /all?fields=...` | **`fields` is required** on `/all` (up to 10 fields) |
| `GET /name/{name}` | `/name/japan`. Partial match. Add `?fullText=true` for an exact match. |
| `GET /alpha/{code}` | `/alpha/JPN` or `/alpha/jp` |
| `GET /alpha?codes={list}` | `/alpha?codes=usa,jpn,bra` |
| `GET /currency/{code}` | `/currency/eur` |
| `GET /lang/{language}` | `/lang/spanish` |
| `GET /capital/{capital}` | `/capital/tokyo` |
| `GET /region/{region}` | `/region/europe` (Africa, Americas, Antarctic, Asia, Europe, Oceania) |
| `GET /subregion/{subregion}` | `/subregion/South America` |
| `GET /demonym/{demonym}` | `/demonym/peruvian` |
| `GET /translation/{name}` | `/translation/alemania` |

Every endpoint accepts `?fields=name,cca3,population` to trim the response. Use it.

## Useful fields

`name`, `cca2`, `cca3`, `ccn3`, `independent`, `unMember`, `capital`, `region`, `subregion`,
`population`, `area`, `latlng`, `borders`, `landlocked`, `currencies`, `languages`, `timezones`,
`continents`, `flags`, `gini`, `car`, `startOfWeek`, `capitalInfo`, `demonyms`, `maps`.

## Example requests

```bash
curl "https://restcountries.com/v3.1/all?fields=name,cca3,region,subregion,population,area,flags"
curl "https://restcountries.com/v3.1/region/europe?fields=name,cca3,population,area,currencies"
curl "https://restcountries.com/v3.1/alpha/JPN"
```

## Response shape (trimmed)

Always an **array**, even for `/alpha/{code}`:

```json
[
  {
    "name": { "common": "Japan", "official": "Japan",
              "nativeName": { "jpn": { "official": "日本", "common": "日本" } } },
    "cca2": "JP", "cca3": "JPN", "ccn3": "392",
    "independent": true, "unMember": true,
    "capital": ["Tokyo"],
    "region": "Asia", "subregion": "Eastern Asia",
    "population": 125836021, "area": 377930.0,
    "latlng": [36.0, 138.0], "landlocked": false,
    "borders": [],
    "currencies": { "JPY": { "name": "Japanese yen", "symbol": "¥" } },
    "languages": { "jpn": "Japanese" },
    "timezones": ["UTC+09:00"],
    "flags": { "png": "https://flagcdn.com/w320/jp.png", "svg": "https://flagcdn.com/jp.svg", "alt": "..." },
    "gini": { "2013": 32.9 }
  }
]
```

## Gotchas

- `/all` without `fields` returns an error. Keep it to 10 or fewer fields.
- `currencies`, `languages`, and `gini` are **objects keyed by code or year**, not arrays.
- `capital` is an array (some countries have several capitals, and some have none).
- `borders` holds `cca3` codes. Look them up to show names.
- A no-match returns HTTP 404 with `{ "status": 404, "message": "Not Found" }`.
- Population figures are snapshots and can be several years old. For time series, use the World Bank API
  (join on `cca3` == World Bank `countryiso3code`).
