# API Reference Docs

There's one file per API. Each file covers the base URL, **every route that's useful for this exercise**,
query parameters, trimmed response shapes, rate limits, and the gotchas that most often cause bugs.
All of these APIs are free and need **no API key or sign-up**.

| API | File | Good for |
|-----|------|----------|
| Open-Meteo | [open-meteo.md](./open-meteo.md) | Weather forecasts, historical climate, air quality, geocoding |
| USGS Earthquakes | [usgs-earthquakes.md](./usgs-earthquakes.md) | Live and historical earthquakes (GeoJSON) |
| Frankfurter | [frankfurter.md](./frankfurter.md) | Currency exchange rates and history |
| CoinGecko (keyless) | [coingecko.md](./coingecko.md) | Crypto prices and history (**low rate limit**) |
| Jolpica F1 | [jolpica-f1.md](./jolpica-f1.md) | Formula 1 results and standings since 1950 |
| World Bank | [world-bank.md](./world-bank.md) | Country-level economic and social indicators over time |
| REST Countries | [rest-countries.md](./rest-countries.md) | Country metadata: population, area, region, currencies, flags |
| CityBikes | [citybikes.md](./citybikes.md) | Live bike-share station availability worldwide |
| Hacker News + Algolia | [hacker-news.md](./hacker-news.md) | Tech news, front-page stats, topic trends |
| PokéAPI | [pokeapi.md](./pokeapi.md) | Pokémon stats, types, and type match-ups |
| Open Library | [open-library.md](./open-library.md) | Books, authors, subjects |
| National Weather Service | [nws-weather-gov.md](./nws-weather-gov.md) | US forecasts and active weather alerts |

For **example challenges** built on these APIs, see [`../APIS.md`](../APIS.md).

## Using these docs with AI

These files are written to be handed straight to an AI assistant as context. Some ways to use them:

1. **Planning.** Give your assistant the file(s) for the API(s) you chose plus [`../README.md`](../README.md),
   and ask it to draft `PLAN.md`. For example:

   > Read `take-home/README.md` and `take-home/apis/usgs-earthquakes.md`. Propose 2–3 backend
   > endpoints that compute something useful from this data for a dashboard. For each one, give the
   > route, query params, the upstream calls it makes, the calculation, the response JSON shape, and the
   > error cases. Then sketch the frontend layout. Call out rate-limit and caching concerns.

2. **Typing the upstream data.** Ask it to turn the "Response shape" section into Pydantic models,
   TypeScript types, or Zod schemas.

3. **Avoiding known bugs.** Point the assistant at the **Gotchas** section when it writes parsing code
   (e.g. "`coordinates` is `[lon, lat, depth]`", "all F1 numbers are strings").

4. **Checking the AI's work.** These docs are a summary. APIs change, and assistants sometimes invent
   parameters. **Always make a real request** (with `curl`, or `../check-apis.sh` for a quick check) before
   you trust a route or field. Record in `AI_LOG.md` any time the AI got an API detail wrong.

> These docs were last reviewed in September 2026. The official docs linked at the top of each
> file are the source of truth.
