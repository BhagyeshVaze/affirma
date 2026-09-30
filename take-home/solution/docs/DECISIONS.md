# Decisions, limits, and next steps

## Decisions

| Decision | Choice | Why |
|---|---|---|
| "This week" | Today plus 6 days, in the city's local time | Matches what a forecast shows. The dates come from the forecast response, never the server clock. |
| Baseline | Last 10 years by default, 5 to 30 selectable | 10 years costs about 10 calls per new city. 30 years is the standard climate-normal length, but costs 30. |
| Window | Plus or minus 3 days around each date | 70 samples per day at 10 years, and a 13-day request still counts as 1 call |
| Day level | Outside the 5th to 95th percentile is unusual; outside the 2nd to 98th is very unusual | Adjusts to each city's spread. The 5 to 95 band was picked by backtest (below). The chart band shows the same 5 to 95 range. |
| Week verdict | **Separate verdicts for days (highs) and nights (lows), never combined.** For each: 0 to 2 flagged days is normal, 3 to 4 somewhat unusual, 5 to 7 very unusual | Picked by backtest (below). The first rule counted a day if its high or its low was flagged, and called 75% of ordinary weeks unusual. |
| Rain | Weekly totals only | Daily rain is mostly zeros, so daily percentiles would be meaningless |
| Units | Fetch metric, convert on the way out | Units stay out of cache keys. Deltas scale by 1.8 with no +32, which is tested. |
| Failed past years | Drop the year and warn, unless fewer than max(3, 70%) remain | One bad upstream call shouldn't blank the page, but a thin baseline shouldn't pass silently |
| Upstream 429 | Return 503 with `Retry-After` | It is the upstream's limit, not the caller's. A 429 on any year fails the whole request, since retrying makes it worse. |
| Location input | Search and pick, then send lat and lon (`city=` also works) | Names are ambiguous: "Paris" returns France first |
| Cache | In memory, one process | No database needed. Run uvicorn with a single worker, or each worker gets its own cache. |

## Verdict backtest

**The target is a design choice:** "unusual" should be rare. Before building, we set a target of
roughly 75 to 85% of ordinary weeks "normal" and under 5% "very unusual", across 7 cities. The
data doesn't dictate these numbers; they come from what the word "unusual" should mean to a
reader.

**Method.** `scripts/backtest_verdict.py` judges every week of a past year the way the app judges
a forecast week. It uses the observed weather in place of a forecast, against the 10 years before
it, with the app's own `anomaly.py` functions.
- Cities: Denver, Chicago, Miami, London, Tokyo, Sydney, and Mumbai, with 51 weeks each (357 in all).
- The rule was picked on 2025 and then checked on 2024.
- No forecast is involved, so this measures the rule itself, not forecast error.

**Not a count of pure false alarms.** Some of these weeks were genuinely unusual; 2024 and 2025
were warm years. So "not normal" in the tables means "flagged", not "wrong".

### Results: all 10 rules, plus the lows version and the shipped code

"Very, worst city" is the share of very-unusual weeks in the worst single city.

| Rule | 2025 normal | 2025 somewhat | 2025 very | 2025 normal, by city | 2024 normal | 2024 somewhat | 2024 very | 2024 normal, by city |
|---|---:|---:|---:|---|---:|---:|---:|---|
| **Old rule:** high or low, p10 to 90, 0-1 / 2-4 / 5-7 days | 25% | 56% | 18% | 14% to 37% | 31% | 52% | 18% | 22% to 45% |
| (a) highs only, p10 to 90, 0-2 / 3-4 / 5-7 | 68% | 24% | 8% | 59% to 76% | 72% | 21% | 7% | 59% to 82% |
| (b) high or low, p5 to 95, 0-1 / 2-4 / 5-7 | 50% | 41% | 9% | 33% to 61% | 57% | 35% | 8% | 39% to 76% |
| (b2) high or low, p5 to 95, 0-2 / 3-4 / 5-7 | 69% | 22% | 9% | 51% to 78% | 74% | 18% | 8% | 61% to 84% |
| (c) week-average high, p10 to 90 / p2 to 98 | 69% | 16% | 15% | 59% to 76% | 74% | 13% | 13% | 63% to 82% |
| (c2) week-average high or low, p5 to 95 / p1 to 99 | 68% | 13% | 19% | 59% to 73% | 72% | 9% | 19% | 63% to 84% |
| (c3) week-average high or low, p10 to 90 / p2 to 98 | 58% | 20% | 23% | 49% to 65% | 62% | 18% | 20% | 53% to 75% |
| (c5) week-average high, p5 to 95 / p1 to 99 | 78% | 10% | 13% | 63% to 84% | 81% | 7% | 12% | 71% to 88% |
| (cD) as (c), with the 10-year trend removed | 66% | 17% | 17% | 63% to 71% | 67% | 15% | 18% | 55% to 75% |
| **(a5) highs only, p5 to 95, 0-2 / 3-4 / 5-7 (shipped, days)** | **83%** | **14%** | **3%** | **73% to 92%** | **83%** | **14%** | **3%** | **76% to 92%** |
| **(a5) lows only, same rule (shipped, nights)** | **85%** | **11%** | **4%** | **69% to 90%** | **87%** | **11%** | **1%** | **76% to 98%** |

- The worst single city for "very unusual" under (a5) is 10% for highs and 12% for lows in 2025
  (Mumbai both times), and 8% and 4% in 2024.
- The script also runs the shipped `summarize_week` and gets exactly the (a5) numbers, so the
  code matches the rule that was tested.

**Before and after.**
- **Before:** only 25% of ordinary 2025 weeks were "normal" and 18% were "very unusual".
- **After:** days are 83% normal and 3% very unusual, and nights are 85% and 4%. The 2024 check
  held (days 83% and 3%, nights 87% and 1%).
- **Still uneven by city:** normal ranges from 73% to 92% for days in 2025. Mumbai is the most
  flagged city.
- **Lows behave like highs.** That is why nights get their own verdict with the same rule,
  rather than a different one.

**Why no rule could hit the target easily: warming.** Recent weeks are warmer than the decade
before them.
- The median 2025 week sits at percentile 63 of the prior 10 years; the median 2024 week sits at
  percentile 69. With no shift, it would be 50.
- 22% of 2025 weeks (21% of 2024 weeks) were above the 90th percentile, against the 10% expected
  with no shift. Only 8% (5%) were below the 10th.
- So part of what any rule flags is a real warm tilt, not noise. (a5) hits the target partly by
  using a wider band (5 to 95), which also hides some of that real warmth. That is a trade-off
  we accepted.

**Why removing the trend made it worse.** Rule (cD) fitted a straight line through each city's
10 baseline years and moved past years up to "now" before comparing. With only 10 points, the
fitted slope is noisy: one hot or cold year near the end can tilt the line a lot. The adjusted
baseline was often wrong in one direction or the other, and "very unusual" rose from 15% to 17%
in 2025 and from 13% to 18% in 2024. A longer baseline, or a trend fitted on 30+ years, might
work, but it costs 3 times the calls.

**A small amount of tuning to 2025.** The rule was chosen from 10 candidates using 2025 data, so
it is slightly tuned to that year. The 2024 check gave nearly the same numbers, which suggests
the tuning is small.

## Known limits

- **The forecast and the history come from different models.** The forecast is a weather model;
  the history is reanalysis, on a slightly different grid point. We compared them on the same
  past days, 30 to 90 days back, where the archive holds its final data. On average they agree
  within about 2°F (mean gap -2.2 to +0.9°F across the 7 cities). But on single days they differ
  more: the day-to-day spread was up to about 4°F (Denver lows). An earlier check used only the
  last 2 weeks, where the archive may still be filled in with model data, and gave numbers that
  were too small. Sydney and Mumbai still agree suspiciously closely (spread 0.3 to 1.0°F), which
  suggests the two sources may share data there; we are not sure.
- **The live app may flag differently than the backtest.** The backtest compares history with
  history. The live app compares a forecast with history. Forecasts smooth out further ahead,
  which means fewer extremes and fewer flags. But the gap between the two sources adds noise,
  which means more flags. We don't know which effect wins.
- **The baseline doesn't account for warming,** so recent warm weeks are more often flagged warm.
- **Forecast uncertainty is ignored.** Day 7 is less certain than day 1.
- **Very unusual rests on few samples.** At 10 years, the 2nd and 98th percentiles of 70 values
  depend on the 1 or 2 most extreme days.
- **The cache is lost on restart,** and is per process.
- **No frontend tests.** The frontend was checked by hand: every state, keyboard search,
  30 years, both units, and the backend being down.

## Not done (cut for time)

- Trend line in the same-week chart. With 10 points it would mostly be noise, as the detrending
  result above shows. It is worth adding only at 20 or more years, and only with a confidence
  interval.
- Serving stale cached data when Open-Meteo is rate limited.
- A per-client rate limit on our own API. Today only the upstream budget is enforced.

## Next steps

1. Backtest with real archived forecasts (for example Open-Meteo's historical forecast API), so
   the live forecast-vs-history gap is measured directly rather than argued about.
2. Try a 30-year baseline in the backtest to see if the warming tilt gets worse or better.
3. Add a few frontend tests (Vitest and Testing Library) for `useApi` and the states.
