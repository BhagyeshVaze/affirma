# Decisions, limits, and next steps

## Decisions

| Decision | Choice | Why |
|---|---|---|
| "This week" | Today plus 6 days, in the city's local time | Matches what a forecast shows. The dates come from the forecast response, never the server clock. |
| Baseline | Last 10 years by default, 5 to 30 selectable | 10 years costs about 10 calls per new city. 30 years is the standard climate-normal length, but costs 30. |
| Window | Plus or minus 3 days around each date | 70 samples per day at 10 years, and a 13-day request still counts as 1 call |
| "Unusual" rule | Outside the 10th to 90th percentile (very: 2nd to 98th) | Adjusts to each city's spread. A fixed rule like "10°F off" would over-flag variable climates like Denver's and under-flag steady ones. |
| Week verdict | Count of flagged days (0 to 1, 2 to 4, 5 to 7) | Easy to explain. A day counts once even if both its high and low are flagged. |
| Rain | Weekly totals only | Daily rain is mostly zeros, so daily percentiles would be meaningless |
| Units | Fetch metric, convert on the way out | Units stay out of cache keys. Deltas scale by 1.8 with no +32, which is tested. |
| Failed past years | Drop the year and warn, unless fewer than max(3, 70%) remain | One bad upstream call shouldn't blank the page, but a thin baseline shouldn't pass silently |
| Upstream 429 | Return 503 with `Retry-After` | It is the upstream's limit, not the caller's. A 429 on any year fails the whole request, since retrying makes it worse. |
| Location input | Search and pick, then send lat and lon (`city=` also works) | Names are ambiguous: "Paris" returns France first |
| Cache | In memory, one process | No database needed. Run uvicorn with a single worker, or each worker gets its own cache. |

## Known limits

- **The forecast and the history come from different sources.** The forecast is a weather model;
  the history is reanalysis, snapped to a slightly different grid point. On the same recent days
  they differed by about 0.5°F for Denver and about 3°F for Chicago (checked 30 Sep 2026). Small
  anomalies of a few degrees should be read with care. The page footnote says so.
- **The baseline is short and recent.** "Unusual" means unusual for the chosen years, not against
  an official 30-year normal.
- **Forecast skill drops with lead time.** Day 7 is less certain than day 1, and the dashboard
  doesn't show forecast uncertainty.
- **The cache is lost on restart,** and is per process.
- **No frontend tests.** The frontend was checked by hand: every state, keyboard search,
  30 years, both units, and the backend being down.

## Not done (cut for time)

- Trend line in the same-week chart. With 10 points it would mostly be noise. It is worth adding
  only at 20 or more years, and only with a confidence interval.
- Serving stale cached data when Open-Meteo is rate limited.
- A per-client rate limit on our own API. Today only the upstream budget is enforced.

## Next steps

1. Add the trend line, with a 95% CI, when `years >= 20`.
2. Add a few frontend tests (Vitest and Testing Library) for `useApi` and the states.
3. Add a like-for-like baseline check: compare past forecasts with what happened, and show how
   big the model offset is per city.
