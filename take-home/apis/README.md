# Choose Your API

Pick **one** of these four APIs. They're all free, need **no API key or sign-up**, are
reliable, and return data that needs real backend work (reshaping, aggregating, joining,
calculating) before it's useful on a dashboard.

| API | Domain | File | Why it's a good backend exercise |
|-----|--------|------|----------------------------------|
| **Open-Meteo** | Weather, climate & air quality | [open-meteo.md](./open-meteo.md) | Columnar arrays to reshape, several sub-APIs to join (geocoding + forecast + archive + air quality), and statistics over long histories |
| **USGS Earthquakes** | Earthquakes worldwide | [usgs-earthquakes.md](./usgs-earthquakes.md) | GeoJSON to flatten, geo math (haversine distance), bucketing, and ranking |
| **Frankfurter** | Currency exchange rates | [frankfurter.md](./frankfurter.md) | Date-keyed time series with gaps, % change, volatility, moving averages, and derived cross rates |
| **Jolpica F1** | Formula 1 results since 1950 | [jolpica-f1.md](./jolpica-f1.md) | Pagination, all-string numbers, joins across results, cumulative stats, and a tight rate limit that makes caching necessary |

Each file contains:

- **At a glance:** base URL, auth, rate limits, format
- **Endpoints:** the routes and query parameters you'll need
- **Example requests:** ready-to-run `curl` commands
- **Response shape:** trimmed JSON examples
- **Gotchas:** details that commonly cause bugs
- **Dashboard ideas:** four suggested dashboards, each with what to display, an example backend
  endpoint, and the backend work it requires

You can build one of the suggested dashboards, combine ideas, or design your own. Just make sure
your backend does more than pass data through.

## Using these docs with AI

These files are written to be handed straight to an AI assistant as context. Some ways to use them:

1. **Planning.** Give your assistant [`../README.md`](../README.md) and the file for your chosen API,
   and ask it to help draft `PLAN.md`. For example:

   > Read `take-home/README.md` and `take-home/apis/usgs-earthquakes.md`. I want to build the
   > "Earthquakes near a place" dashboard. Propose the backend endpoints: for each one give the
   > route, query params, the upstream calls, the calculations, the response JSON shape, and the
   > error cases. Then sketch the frontend components. Call out rate-limit and caching concerns
   > and anything in the Gotchas section that affects the design.

2. **Typing the upstream data.** Ask it to turn the "Response shape" section into Pydantic models,
   TypeScript types, or Zod schemas.

3. **Avoiding known bugs.** Point the assistant at the **Gotchas** section when it writes parsing code.

4. **Checking the AI's work.** These docs are a summary. APIs change, and assistants sometimes invent
   parameters. **Always make a real request** (with `curl`, or `../check-apis.sh`) before you trust a
   route or field. Record in `AI_LOG.md` any time the AI got an API detail wrong.

> Every route, sample request, and response example in these docs was checked against the live APIs
> on 29 September 2026. APIs can change, so the official docs linked at the top of each file are the
> source of truth.
