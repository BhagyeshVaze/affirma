# Public APIs & Example Challenges

Every API below is **free and needs no API key, token, or sign-up**. You can call
them directly with `curl` or `fetch`. Each section has a sample request and one
or more **example challenges**. Use one as-is or as inspiration for your own.

> Rate limits are approximate and set by the providers, who can change them. Cache
> upstream responses in your backend. Good citizenship is part of the grade.

## Quick reference

| # | API | Domain | Rate limit (approx.) | Notes |
|---|-----|--------|----------------------|-------|
| 1 | [Open-Meteo](https://open-meteo.com/en/docs) | Weather, climate, air quality | ~10k req/day | Forecast, historical data back to 1940, geocoding |
| 2 | [USGS Earthquakes](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php) | Earthquakes | Generous | GeoJSON, near real-time |
| 3 | [Frankfurter](https://frankfurter.dev/) | Currency exchange rates | No hard limit | Central bank reference rates, history back decades |
| 4 | [CoinGecko (keyless)](https://docs.coingecko.com/docs/keyless-public-api) | Crypto prices | **Low** (a few req/min) | Cache is essential |
| 5 | [Jolpica F1](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md) | Formula 1 results | 200 req/hour | Drop-in Ergast replacement |
| 6 | [World Bank Indicators](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | Economics, population | Generous | Add `format=json` |
| 7 | [REST Countries](https://restcountries.com/) | Country metadata | Generous | `fields=` is **required** on `/all` |
| 8 | [CityBikes](https://api.citybik.es/v2/) | Bike-share stations | Generous | 700+ networks worldwide, live |
| 9 | [Hacker News](https://github.com/HackerNews/API) + [Algolia HN Search](https://hn.algolia.com/api) | Tech news | Generous | Firebase API returns IDs only, so you fetch items one by one |
| 10 | [PokéAPI](https://pokeapi.co/docs/v2) | Pokémon | Generous (please cache) | Fun, deeply nested data |
| 11 | [Open Library](https://openlibrary.org/developers/api) | Books | 1 req/s (3 req/s with User-Agent) | Set a descriptive `User-Agent` |
| 12 | [National Weather Service](https://www.weather.gov/documentation/services-web-api) | US forecasts & alerts | Generous | **`User-Agent` header required**. US only |

---

## 1. Open-Meteo: weather & climate

```bash
# Geocode a city name -> lat/lon
curl "https://geocoding-api.open-meteo.com/v1/search?name=Chicago&count=1"
# 7-day forecast
curl "https://api.open-meteo.com/v1/forecast?latitude=41.88&longitude=-87.63&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
# Historical daily data
curl "https://archive-api.open-meteo.com/v1/archive?latitude=41.88&longitude=-87.63&start_date=2024-01-01&end_date=2024-12-31&daily=temperature_2m_mean,precipitation_sum"
# Air quality
curl "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=41.88&longitude=-87.63&hourly=pm2_5,us_aqi"
```

**Example challenges**
- **City comparison:** `GET /api/compare?cities=Chicago,Austin,Seattle` geocodes each
  city, fetches the forecast, and returns each city's weekly high/low, total
  precipitation, and a "nicest day" chosen by a scoring rule that you define and document.
- **Climate anomaly:** `GET /api/anomaly?city=Denver` compares this week's forecast
  with the same calendar week averaged over the last 10 years and returns the
  temperature difference per day.

## 2. USGS Earthquakes

```bash
# Summary feeds: {significant|4.5|2.5|1.0|all}_{hour|day|week|month}.geojson
curl "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson"
# Query API with filters
curl "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-01-01&minmagnitude=5"
```

**Example challenges**
- **Activity summary:** `GET /api/quakes/summary?days=7` returns counts per day,
  counts per magnitude bucket (<2, 2–4, 4–6, 6+), and the top 10 strongest quakes.
- **Near me:** `GET /api/quakes/nearby?lat=..&lon=..&radius_km=500` filters quakes by
  great-circle (haversine) distance and sorts them by distance.

## 3. Frankfurter: exchange rates

```bash
curl "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,GBP,JPY"
curl "https://api.frankfurter.dev/v1/2024-01-01..2024-06-30?base=USD&symbols=EUR,GBP"
curl "https://api.frankfurter.dev/v1/currencies"
# A newer v2 API also exists (e.g. /v2/rates?base=USD). v1 is frozen but stays available.
```

**Example challenges**
- **Currency performance:** `GET /api/fx/performance?base=USD&symbols=EUR,GBP,JPY&from=..&to=..`
  returns the % change and the volatility (standard deviation of daily returns) for each
  currency, ranked from best to worst.
- **Trip budget:** `GET /api/fx/budget?home=USD&amount=2000&destinations=EUR,JPY,MXN`
  shows how much the budget is worth in each destination today compared with 30 and
  90 days ago.

## 4. CoinGecko (keyless public API)

```bash
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
curl "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=20"
curl "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"
```

> The keyless rate limit is **low**. Cache aggressively and don't poll.
> Don't send any `x-cg-*-api-key` header.

**Example challenges**
- **Trend indicators:** `GET /api/crypto/{id}/indicators?days=90` returns the price
  series with 7-day and 30-day moving averages and the maximum drawdown.
- **Portfolio:** `POST /api/portfolio` accepts `[{id, amount, bought_at_price}]` and
  returns the current value and profit/loss per holding and in total.

## 5. Jolpica F1: Formula 1 results

```bash
curl "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"
curl "https://api.jolpi.ca/ergast/f1/2025/results.json?limit=100"
curl "https://api.jolpi.ca/ergast/f1/2025/5/results.json"
```

**Example challenges**
- **Title race chart:** `GET /api/f1/{season}/progression` returns each driver's
  cumulative points after every round, ready for a line chart.
- **Teammate battle:** `GET /api/f1/{season}/teammates` returns, for each team, the
  head-to-head record of its two drivers in qualifying and races.

## 6. World Bank Indicators

```bash
# GDP per capita for a few countries
curl "https://api.worldbank.org/v2/country/USA;CHN;IND/indicator/NY.GDP.PCAP.CD?format=json&date=2000:2023&per_page=500"
# Population
curl "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json&date=2023&per_page=300"
```

## 7. REST Countries

```bash
curl "https://restcountries.com/v3.1/all?fields=name,cca3,region,population,area,flags"
curl "https://restcountries.com/v3.1/region/europe?fields=name,population,area"
```

**Example challenges (6 + 7 together)**
- **Country explorer:** `GET /api/countries?region=Asia&sort=density` joins REST Countries
  metadata with World Bank GDP data to return population density, GDP per capita, and
  the compound annual growth rate (CAGR) of GDP per capita over the last 10 years.
- **Region rollup:** `GET /api/regions` returns each region's total population, total
  area, and population-weighted average GDP per capita.

## 8. CityBikes: bike-share networks

```bash
curl "https://api.citybik.es/v2/networks?fields=id,name,location"
curl "https://api.citybik.es/v2/networks/citi-bike-nyc"
```

**Example challenges**
- **Station health:** `GET /api/bikes/{network}/summary` returns the total bikes and
  docks, the % of stations that are empty or full, and the 10 stations closest to
  empty.
- **Find a bike:** `GET /api/bikes/{network}/nearest?lat=..&lon=..` returns the 5
  nearest stations that have at least one free bike.

## 9. Hacker News

```bash
curl "https://hacker-news.firebaseio.com/v0/topstories.json"   # list of IDs
curl "https://hacker-news.firebaseio.com/v0/item/8863.json"     # one item
curl "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=50"
```

**Example challenges**
- **Front page stats:** `GET /api/hn/front-page` fetches the top 30 stories
  concurrently and returns the most common domains, the average score, and the
  story-age distribution.
- **Topic trends:** `GET /api/hn/trend?term=rust&months=12` uses Algolia search to return
  the number of stories per month mentioning the term.

## 10. PokéAPI

```bash
curl "https://pokeapi.co/api/v2/pokemon/pikachu"
curl "https://pokeapi.co/api/v2/type/electric"
```

**Example challenges**
- **Team analyzer:** `POST /api/team` accepts up to 6 Pokémon names and returns the
  team's average base stats plus type weaknesses and resistances, built from the
  type damage relations.

## 11. Open Library

```bash
curl -A "MyTakeHome/1.0 (you@example.com)" "https://openlibrary.org/search.json?author=ursula+le+guin&limit=100"
curl -A "MyTakeHome/1.0 (you@example.com)" "https://openlibrary.org/subjects/science_fiction.json?limit=50"
```

**Example challenges**
- **Author timeline:** `GET /api/authors/{name}/timeline` returns works grouped by
  decade of first publication, with each decade's most-edited work.

## 12. National Weather Service (US only)

```bash
curl -A "MyTakeHome/1.0 (you@example.com)" "https://api.weather.gov/points/39.74,-104.99"
curl -A "MyTakeHome/1.0 (you@example.com)" "https://api.weather.gov/alerts/active?area=CA"
```

**Example challenges**
- **Alert board:** `GET /api/alerts?states=CA,TX,FL` groups active alerts by state
  and severity and returns the counts plus the most severe alert per state.

---

### Ideas for combining APIs

- Earthquakes (USGS) + country data (REST Countries): which regions had the most seismic activity this month?
- Weather (Open-Meteo) + bike share (CityBikes): station availability shown next to current weather for that city.
- Exchange rates (Frankfurter) + World Bank: GDP per capita converted into a currency the user chooses.
