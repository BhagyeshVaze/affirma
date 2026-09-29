# World Bank Indicators API

Thousands of development indicators (GDP, population, life expectancy, CO₂, internet use, ...)
for about 217 countries and many regional aggregates, usually as yearly values going back to 1960.

- **Official docs:** https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
  ([basic call structure](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581),
  [indicator queries](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599))
- **Auth:** none
- **Rate limits:** none published. Be reasonable. The data changes rarely, so cache for a long time.
- **Format:** XML by default. **Always add `format=json`.**

Base URL: `https://api.worldbank.org/v2`

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /country` | List countries (and aggregates) with region, income level, capital, lat/long |
| `GET /country/{codes}` | One or more countries, e.g. `USA;JPN;BRA` |
| `GET /country/{codes}/indicator/{indicator}` | **Main data call**: indicator values for those countries |
| `GET /indicator/{indicator}` | Indicator metadata (name, description, source) |
| `GET /indicator?per_page=100` | Browse all indicators (there are thousands) |
| `GET /region`, `GET /incomelevel`, `GET /lendingtype` | Reference lists |
| `GET /region/{code}/country` | Countries in a region |

Country codes are ISO3 (`USA`) or ISO2 (`US`). Use `all` for everything and `;` to separate several.

### Query parameters

| Param | Example | Notes |
|-------|---------|-------|
| `format` | `json` | Required for JSON |
| `date` | `2023`, `2000:2023` | Year or range |
| `mrv` | `5` | Most recent N values (instead of `date`) |
| `mrnev` | `1` | Most recent N **non-empty** values |
| `per_page` | `1000` | Default is 50. Raise it or paginate. |
| `page` | `2` | Pagination |

### Handy indicator codes

| Code | Indicator |
|------|-----------|
| `SP.POP.TOTL` | Population, total |
| `NY.GDP.MKTP.CD` | GDP (current US$) |
| `NY.GDP.PCAP.CD` | GDP per capita (current US$) |
| `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) |
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices (annual %) |
| `SL.UEM.TOTL.ZS` | Unemployment (% of labor force) |
| `SP.DYN.LE00.IN` | Life expectancy at birth |
| `SP.URB.TOTL.IN.ZS` | Urban population (% of total) |
| `IT.NET.USER.ZS` | Internet users (% of population) |
| `EG.ELC.ACCS.ZS` | Access to electricity (% of population) |
| `EG.FEC.RNEW.ZS` | Renewable energy (% of final energy use) |

Search for more codes at https://data.worldbank.org/indicator. The code appears in each indicator page's URL.

## Example requests

```bash
curl "https://api.worldbank.org/v2/country/USA;CHN;IND/indicator/NY.GDP.PCAP.CD?format=json&date=2000:2023&per_page=500"
curl "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&mrnev=1&per_page=400"
curl "https://api.worldbank.org/v2/country?format=json&per_page=400"
```

## Response shape

The response is a **2-element array**: `[paginationMeta, rows]`.

```json
[
  { "page": 1, "pages": 1, "per_page": 500, "total": 72, "sourceid": "2", "lastupdated": "2026-07-01" },
  [
    { "indicator": { "id": "NY.GDP.PCAP.CD", "value": "GDP per capita (current US$)" },
      "country": { "id": "US", "value": "United States" },
      "countryiso3code": "USA",
      "date": "2023",
      "value": 82769.41,
      "unit": "", "obs_status": "", "decimal": 1 }
  ]
]
```

`/country` rows:

```json
{ "id": "USA", "iso2Code": "US", "name": "United States",
  "region": { "id": "NAC", "value": "North America" },
  "incomeLevel": { "id": "HIC", "value": "High income" },
  "capitalCity": "Washington D.C.", "longitude": "-77.032", "latitude": "38.8895" }
```

## Gotchas

- **Check element `[0]` vs `[1]`.** On an error, you get a single-element array with a
  `message` object instead of `[meta, rows]`.
- `value` is often **`null`**, especially for the most recent year. Use `mrnev` or filter out nulls.
- `date` is a **string** (`"2023"`), and rows come newest first.
- `country/all` includes **aggregates** such as "World", "Euro area", and "High income". To keep
  real countries only, fetch `/country` and drop entries where `region.value == "Aggregates"`.
- The default `per_page` of 50 silently truncates results. Always set it, or follow `pages`.
- Join to REST Countries with `countryiso3code` == `cca3`.
