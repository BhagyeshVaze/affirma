# Decisions, limits, and next steps

## My review

I used Claude to define the first version of the plan. The main thing that came up in review was
the week verdict. The first rule looked like it would call too many normal weeks unusual, so I had
it tested on a real year of weather. It was worse than I expected: only about a quarter of weeks
came out normal.

I had a few other rules tried and went with the one that held up on two different years. I also
kept nights as their own verdict, because warm nights were often the most interesting part and I
didn't want the fix to hide them.

What counts as "unusual" is a judgment call. I wanted it to mean rare, so that's what the rule is
tuned for. Some of the flagged weeks were probably real, since recent years have run warmer.

After the build, I had Claude review the whole app. The bugs that mattered were fixed, and the
rest are listed in the README.

## Decisions

**This week.** Today plus the next 6 days, in the city's local time. The dates come from the
forecast itself, not the server clock, so it's always the city's actual today.

**Baseline.** Last 10 years by default, and you can pick 5 to 30. 10 years costs 11 API calls per
new city (1 forecast plus 10 years). 30 is the standard climate length, but it costs 31.

**Window.** Plus or minus 3 days around each date. That gives 70 past values per day at 10 years
instead of 10, and a 13-day request still counts as 1 call.

**Day level.** A day is unusual if it falls outside the 5th to 95th percentile of its past values,
and very unusual outside the 2nd to 98th. Percentiles adjust to how much each city's weather
swings. The shaded band on the chart is the same 5 to 95 range, so what you see is what gets
flagged.

**Week verdict.** Days (highs) and nights (lows) each get their own verdict and are never
combined. 0 to 2 flagged days is normal, 3 to 4 is somewhat unusual, and 5 to 7 is very unusual.
The backtest below is why.

**Thin baseline.** If fewer than 5 of 7 days can be judged, the verdict says "not enough history"
instead of guessing, and the banner says whether the history or the forecast is what's missing.
A day can be judged when it has a forecast value and at least 30 past values. The review caught
this: at 5 years with 1 year failing, every day had 28 values and the old code still said
"normal". That case now always gives "not enough history" (4 years × 7 days = 28), on purpose.

**Failed past years.** If a past year fails to load, it's dropped with a warning, as long as at
least max(3, 70% of years) remain. One bad call shouldn't blank the page.

**Rain.** Weekly totals only. Most days have zero rain, so daily percentiles wouldn't mean
anything.

**Units.** Everything is fetched in metric and converted at the end, so units never enter the
cache. Differences convert with × 1.8 only, no +32. That's tested.

**Rate limits.** If Open-Meteo returns 429, the app returns 503 with a `Retry-After` header. It's
their limit, not the user's fault. A 429 on any year fails the whole request, since retrying would
make it worse.

**Location.** You search, pick a place, and the app sends lat and lon. Names are ambiguous
("Paris" returns France first), so picking avoids guessing. `city=` still works for direct calls.

**Cache.** In memory, one process. No database needed for this. Run uvicorn with one worker, or
each worker gets its own cache.

## Verdict backtest

**The problem.** The first rule flagged a day if its high or its low was outside the 10th to 90th
percentile. That looked like it would flag too many normal weeks, so it got tested.

**How it was tested.** `scripts/backtest_verdict.py` takes every week of a past year and judges it
the way the app judges a forecast, using the real weather instead of a forecast. Each week is
compared with the 10 years before it, using the app's own `anomaly.py`.

- 7 cities: Denver, Chicago, Miami, London, Tokyo, Sydney, and Mumbai. 51 weeks each, 357 total.
- Rules were picked on 2025 and checked on 2024.
- No forecast is involved, so this tests the rule itself.

**The target.** Roughly 75 to 85% of weeks "normal" and under 5% "very unusual". This is a design
choice, not something the data gives you. Some real weeks were genuinely unusual, so a flag here
means "flagged", not "wrong".

### Results

Each cell is normal / somewhat / very, in percent. "By city" is the range of normal across the 7
cities. Rounding means some rows add to 101.

| Rule | 2025 | 2025 by city | 2024 | 2024 by city |
|---|---|---|---|---|
| Old: high or low, p10-90, 0-1 / 2-4 / 5-7 days | 24 / 53 / 24 | 14 to 35 | 28 / 52 / 20 | 20 to 41 |
| (a) highs only, p10-90, 0-2 / 3-4 / 5-7 | 65 / 24 / 10 | 57 to 76 | 68 / 24 / 9 | 55 to 82 |
| (b) high or low, p5-95, 0-1 / 2-4 / 5-7 | 46 / 44 / 10 | 31 to 57 | 52 / 38 / 10 | 35 to 71 |
| (b2) high or low, p5-95, 0-2 / 3-4 / 5-7 | 65 / 25 / 10 | 45 to 76 | 71 / 19 / 10 | 59 to 82 |
| (c) week-average high, p10-90 / p2-98 | 66 / 18 / 16 | 59 to 71 | 71 / 15 / 14 | 55 to 80 |
| (c2) week-average high or low, p5-95 / p1-99 | 66 / 13 / 21 | 59 to 71 | 70 / 10 / 20 | 59 to 80 |
| (c3) week-average high or low, p10-90 / p2-98 | 52 / 23 / 25 | 41 to 63 | 59 / 19 / 22 | 49 to 75 |
| (c5) week-average high, p5-95 / p1-99 | 76 / 9 / 15 | 63 to 82 | 80 / 7 / 13 | 69 to 86 |
| (cD) same as (c), trend removed | 63 / 18 / 18 | 59 to 69 | 64 / 16 / 20 | 49 to 73 |
| **(a5) highs only, p5-95, 0-2 / 3-4 / 5-7 (shipped, days)** | **80 / 15 / 4** | **67 to 88** | **82 / 14 / 3** | **75 to 90** |
| **(a5) lows only, same rule (shipped, nights)** | **83 / 13 / 4** | **69 to 88** | **86 / 12 / 2** | **76 to 96** |

**What I took from it.**

- The old rule called only 24% of weeks normal. (a5) gets that to 80% for days and 83% for
  nights, with 4% very unusual. 2024 gave nearly the same numbers (82% and 86%, with 2 to 3%
  very unusual).
- (a5) is the only rule that meets the target in both years. The next best, (c5), gets enough
  normal weeks but 13 to 15% very unusual.
- Lows behave like highs, so nights use the same rule.
- Cities still differ. Days range from 67% to 88% normal in 2025. Mumbai is flagged most, with
  12% very unusual for highs and 14% for lows.
- The script also runs the shipped `summarize_week` and gets exactly the (a5) numbers, so the code
  matches what was tested.
- The rule was picked from 10 candidates using 2025, so there's a little tuning to that year. The
  2024 check held, so it's small.
- These numbers are from after one later fix. Days used to be flagged by rank, which didn't
  always match the band on the chart. Now both use the same lines, which flags a few more days:
  (a5) days went from 83% to 80% normal in 2025. It still came out best.

**Warming is part of it.** Recent years are warmer than the decade before them. The median 2025
week sits at the 63rd percentile of the prior 10 years, and 2024 at the 69th. With no change it
would be 50. About 25% of 2025 weeks (23% in 2024) were above the 90th percentile, against the 10%
you'd expect. Only 9% (6%) were below the 10th. So some of what the old rule flagged was real
warmth. The wider 5 to 95 band in (a5) hides some of that too. I accepted that trade-off.

**Why the trend isn't removed.** Rule (cD) tried it: fit a line through each city's 10 years and
move past years up to now. It made things worse. With only 10 points, one hot or cold year can
tilt the line a lot, and "very unusual" went up (16% to 18% in 2025, 14% to 20% in 2024). A
30-year trend might work, but it costs 3 times the calls.

## Known limits

- **Two different data sources.** The forecast comes from a weather model and the history from
  reanalysis, on slightly different grid points. On the same past days (30 to 90 days back), they
  agree within about 2°F on average (mean gap -2.2 to +0.9°F across the 7 cities), but single days
  can differ by up to about 4°F (Denver lows). An earlier check used only the last 2 weeks, where
  the archive may still hold model data, and gave numbers that were too small. Sydney and Mumbai
  agree suspiciously closely (0.3 to 1.0°F), so the sources may share data there. Not sure.
- **The live app may flag differently than the backtest.** The backtest compares history with
  history. The live app compares a forecast with history. Forecasts smooth out further ahead,
  which means fewer flags, but the gap between sources adds noise, which means more. It's unclear
  which wins.
- **No warming adjustment.** Recent warm weeks get flagged warm more often.
- **Forecast uncertainty is ignored.** Day 7 is less certain than day 1.
- **"Very unusual" rests on few values.** At 10 years, the 2nd and 98th percentiles depend on the
  2 or 3 most extreme days out of 70.
- **The cache is lost on restart** and isn't shared between processes.
- **Few frontend tests.** Six Vitest tests cover the search box and the verdict banner. The rest
  was checked by hand: every state, keyboard search, 30 years, both units, the mobile layout, and
  the backend going down.

## Potential future steps

- Trend line on the same-week chart. With 10 points it's mostly noise (see above). Worth it only
  at 20+ years, with a confidence interval.
- Serving old cached data when Open-Meteo is rate limited.
- A rate limit on our own API. Right now only the upstream budget is enforced.
- Backtest against real archived forecasts (Open-Meteo has a historical forecast API), so the
  forecast vs history gap is measured instead of guessed.
- Try a 30-year baseline in the backtest to see how the warming tilt changes.
- Add more frontend tests for `useApi` and the loading, empty, and error states.
