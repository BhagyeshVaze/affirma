# Decisions, limits, and next steps

## Decisions

| Decision | Choice | Why |
|---|---|---|
| "This week" | Today plus 6 days, in the city's local time | Matches what a forecast shows. The dates come from the forecast response, never the server clock. |
| Baseline | Last 10 years by default, 5 to 30 selectable | 10 years costs 11 calls per new city (1 forecast plus 10 years). 30 years is the standard climate-normal length, but costs 31. |
| Window | Plus or minus 3 days around each date | 70 samples per day at 10 years, and a 13-day request still counts as 1 call |
| Day level | A day is unusual when its value is outside the 5th to 95th percentile lines of its baseline, and very unusual outside the 2nd to 98th | Adjusts to each city's spread. The 5 to 95 band was picked by backtest (below). The chart's shaded band is drawn from the same lines, and the shown percentile uses the same scale, so a dot outside the band is always flagged (checked by a 3,000-case test). |
| Week verdict | **Separate verdicts for days (highs) and nights (lows), never combined.** For each: 0 to 2 flagged days is normal, 3 to 4 somewhat unusual, 5 to 7 very unusual | Picked by backtest (below). The first rule counted a day if its high or its low was flagged, and called about 3 in 4 ordinary weeks unusual. |
| Rain | Weekly totals only | Daily rain is mostly zeros, so daily percentiles would be meaningless |
| Units | Fetch metric, convert on the way out | Units stay out of cache keys. Deltas scale by 1.8 with no +32, which is tested. |
| Failed past years | Drop the year and warn, unless fewer than max(3, 70%) remain | One bad upstream call shouldn't blank the page, but a thin baseline shouldn't pass silently |
| Thin baseline | If fewer than 5 of 7 days can be judged, the verdict is "not enough history", and the banner says whether the history or the forecast is what is missing | Added after review. At 5 years with 1 year failing, every day had 28 samples and the old code called the week "normal". That case now always gives "not enough history" (4 years x 7 days = 28, under the 30 needed); we kept it as a clear message rather than an error. |
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

These are the current numbers, after a later fix made the flag lines match the chart's band
(see "A later fix" below). Every rule's day flags use the same lines.

| Rule | 2025 normal | 2025 somewhat | 2025 very | 2025 normal, by city | 2024 normal | 2024 somewhat | 2024 very | 2024 normal, by city |
|---|---:|---:|---:|---|---:|---:|---:|---|
| **Old rule:** high or low, p10 to 90, 0-1 / 2-4 / 5-7 days | 24% | 53% | 24% | 14% to 35% | 28% | 52% | 20% | 20% to 41% |
| (a) highs only, p10 to 90, 0-2 / 3-4 / 5-7 | 65% | 24% | 10% | 57% to 76% | 68% | 24% | 9% | 55% to 82% |
| (b) high or low, p5 to 95, 0-1 / 2-4 / 5-7 | 46% | 44% | 10% | 31% to 57% | 52% | 38% | 10% | 35% to 71% |
| (b2) high or low, p5 to 95, 0-2 / 3-4 / 5-7 | 65% | 25% | 10% | 45% to 76% | 71% | 19% | 10% | 59% to 82% |
| (c) week-average high, p10 to 90 / p2 to 98 | 66% | 18% | 16% | 59% to 71% | 71% | 15% | 14% | 55% to 80% |
| (c2) week-average high or low, p5 to 95 / p1 to 99 | 66% | 13% | 21% | 59% to 71% | 70% | 10% | 20% | 59% to 80% |
| (c3) week-average high or low, p10 to 90 / p2 to 98 | 52% | 23% | 25% | 41% to 63% | 59% | 19% | 22% | 49% to 75% |
| (c5) week-average high, p5 to 95 / p1 to 99 | 76% | 9% | 15% | 63% to 82% | 80% | 7% | 13% | 69% to 86% |
| (cD) as (c), with the 10-year trend removed | 63% | 18% | 18% | 59% to 69% | 64% | 16% | 20% | 49% to 73% |
| **(a5) highs only, p5 to 95, 0-2 / 3-4 / 5-7 (shipped, days)** | **80%** | **15%** | **4%** | **67% to 88%** | **82%** | **14%** | **3%** | **75% to 90%** |
| **(a5) lows only, same rule (shipped, nights)** | **83%** | **13%** | **4%** | **69% to 88%** | **86%** | **12%** | **2%** | **76% to 96%** |

- The worst single city for "very unusual" under (a5) is 12% for highs and 14% for lows in 2025,
  and 8% and 4% in 2024.
- The script also runs the shipped `summarize_week` and gets exactly the (a5) numbers, so the
  code matches the rule that was tested. No week in either year came out "not enough history".

**Before and after.**
- **Before:** only 24% of ordinary 2025 weeks were "normal" and 24% were "very unusual".
- **After:** days are 80% normal and 4% very unusual, and nights are 83% and 4%. The 2024 check
  held (days 82% and 3%, nights 86% and 2%).
- **Still uneven by city:** normal ranges from 67% to 88% for days in 2025.
- **Lows behave like highs.** That is why nights get their own verdict with the same rule,
  rather than a different one.
- **(a5) is the only rule that meets the target in both years.** The next best, (c5), gets
  enough "normal" weeks but 13 to 15% "very unusual".

**A later fix changed these numbers a little.** The rule was first chosen when days were
flagged by rank, while the chart's band was drawn from interpolated percentile lines. The two
disagreed: about 11% of dots drawn outside the band were still "normal". Now both use the same
lines. That flags slightly more days: (a5) days went from 83% normal and 3% very unusual in 2025
to 80% and 4%, and nights from 85% and 4% to 83% and 4%. (a5) still meets the target, and it is
still the best rule.

**Why no rule could hit the target easily: warming.** Recent weeks are warmer than the decade
before them.
- The median 2025 week sits at percentile 63 of the prior 10 years; the median 2024 week sits at
  percentile 69. With no shift, it would be 50.
- 25% of 2025 weeks (23% of 2024 weeks) were above the 90th percentile, against the 10% expected
  with no shift. Only 9% (6%) were below the 10th.
- So part of what any rule flags is a real warm tilt, not noise. (a5) hits the target partly by
  using a wider band (5 to 95), which also hides some of that real warmth. That is a trade-off
  we accepted.

**Why removing the trend made it worse.** Rule (cD) fitted a straight line through each city's
10 baseline years and moved past years up to "now" before comparing. With only 10 points, the
fitted slope is noisy: one hot or cold year near the end can tilt the line a lot. The adjusted
baseline was often wrong in one direction or the other, and "very unusual" rose from 16% to 18%
in 2025 and from 14% to 20% in 2024. A longer baseline, or a trend fitted on 30+ years, might
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
  depend on the 2 or 3 most extreme days.
- **The cache is lost on restart,** and is per process.
- **Few frontend tests.** There are 6: the city search's keyboard and debounce behavior, and
  the verdict banner. The charts and the rest were checked by hand: every state, keyboard
  search, 30 years, both units, the mobile layout, and the backend being down.

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
3. Add more frontend tests: `useApi`, the loading and error states, and the charts.
