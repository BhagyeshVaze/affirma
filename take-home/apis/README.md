# APIs

Pick one. All are free, with no key and no sign-up.

| | [Open-Meteo](./open-meteo.md) | [USGS Earthquakes](./usgs-earthquakes.md) | [Frankfurter](./frankfurter.md) | [Jolpica F1](./jolpica-f1.md) |
|---|---|---|---|---|
| **Data** | Weather | Earthquakes | Exchange rates | Formula 1 |
| **Format** | Parallel arrays | GeoJSON | Rates keyed by date | Nested, paginated |
| **Rate limit** | 10,000/day | None published | None published | 500/hour |
| **Hard part** | Reshaping arrays, joining sub-APIs | Geo math, grouping | Gaps, returns, volatility | Paging, string numbers, sprints |

Each doc has: endpoints, examples, response shapes, sample data, gotchas, and four dashboard ideas.

## Other free APIs

You can also use another free API that needs no key. We haven't documented these in depth, so check
that one works before you commit to it.

| API | Data |
| --- | --- |
| [World Bank](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | Country economics and population, yearly |
| [CityBikes](https://api.citybik.es/v2/) | Live bike-share stations worldwide |
| [Hacker News](https://github.com/HackerNews/API) / [Algolia HN Search](https://hn.algolia.com/api) | Tech news stories and comments |
| [PokéAPI](https://pokeapi.co/docs/v2) | Pokémon stats and types |
| [Open Library](https://openlibrary.org/developers/api) | Books and authors |
| [National Weather Service](https://www.weather.gov/documentation/services-web-api) | US forecasts and alerts. Needs a `User-Agent` header |
| [Nager.Date](https://date.nager.at/Api) | Public holidays by country |
| [Art Institute of Chicago](https://api.artic.edu/docs/) | Artworks and artists |
| [The Met Collection](https://metmuseum.github.io/) | Artworks and departments |
| [US Treasury Fiscal Data](https://fiscaldata.treasury.gov/api-documentation/) | US debt, spending, and revenue |
| [openFDA](https://open.fda.gov/apis/) | Drug and food safety reports |
| [OpenF1](https://openf1.org/) | Live and recent F1 timing data |
| [UK Carbon Intensity](https://carbon-intensity.github.io/api-definitions/) | UK electricity carbon intensity and fuel mix |
| [Open Food Facts](https://openfoodfacts.github.io/openfoodfacts-server/api/) | Food products and nutrition |

## Using these docs with AI

1. **Plan.** Give your AI `../README.md` and your API's doc. Ask for a plan. Save the plan (and any
   key prompts) in `docs/`. Example prompt:

   > Read `take-home/README.md` and `take-home/apis/usgs-earthquakes.md`. Plan the "Earthquakes
   > near a place" dashboard. For each endpoint give the route, params, upstream calls, math,
   > response shape, and errors. Then outline the React components. Flag caching and gotchas.

2. **Types.** Ask it to turn the response shapes into Pydantic models.
3. **Gotchas.** Point it at the Gotchas section when it writes parsing code.
4. **Verify.** AI invents parameters. Test every route with a real request. Note its mistakes in `docs/`.

> [!NOTE]
> Checked against the live APIs on 29 Sep 2026. If something differs, the official docs win.
