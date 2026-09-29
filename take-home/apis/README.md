# APIs

Pick one. All are free, with no key and no sign-up.

| | [Open-Meteo](./open-meteo.md) | [USGS Earthquakes](./usgs-earthquakes.md) | [Frankfurter](./frankfurter.md) | [Jolpica F1](./jolpica-f1.md) |
|---|---|---|---|---|
| **Data** | Weather | Earthquakes | Exchange rates | Formula 1 |
| **Format** | Parallel arrays | GeoJSON | Rates keyed by date | Nested, paginated |
| **Rate limit** | 10,000/day | None published | None published | 500/hour |
| **Hard part** | Reshaping arrays, joining sub-APIs | Geo math, grouping | Gaps, returns, volatility | Paging, string numbers, sprints |

Each doc has: endpoints, examples, response shapes, sample data, gotchas, and four dashboard ideas.

## Using these docs with AI

1. **Plan.** Give your AI `../README.md` and your API's doc. Ask for a plan. Commit the prompt and
   plan to `ai/`. Example prompt:

   > Read `take-home/README.md` and `take-home/apis/usgs-earthquakes.md`. Plan the "Earthquakes
   > near a place" dashboard. For each endpoint give the route, params, upstream calls, math,
   > response shape, and errors. Then outline the React components. Flag caching and gotchas.

2. **Types.** Ask it to turn the response shapes into Pydantic models.
3. **Gotchas.** Point it at the Gotchas section when it writes parsing code.
4. **Verify.** AI invents parameters. Test every route with a real request. Log mistakes in `AI_LOG.md`.

> [!NOTE]
> Checked against the live APIs on 29 Sep 2026. If something differs, the official docs win.
