# How AI was used

Tool: Claude (Opus 5.5) in Claude Code. It read the task docs, wrote the plan, and wrote the
code in small commits. The plan's suggested defaults (PLAN.md section 2) were kept to fit the
time box. Each is one constant, so it is easy to change.

No secrets or private data were shared: the app needs no API keys, and only public Open-Meteo
data was used.

## Key prompts

1. Understanding the task:

   > go through this and tell me what you understand

   This was sent with the task email, then again with `take-home/README.md`, `apis/README.md`,
   and `apis/open-meteo.md`. The AI compared the four ideas by call cost and difficulty and
   recommended "Is this week unusual?".

2. The plan (the example prompt from `apis/README.md`, adapted):

   > Plan the "Is this week unusual?" dashboard. For each endpoint give the route, params,
   > upstream calls, math, response shape, and errors. Then outline the React components.
   > Flag caching and gotchas.

   The result is [PLAN.md](PLAN.md), committed before any code.

3. The build:

   > only have the next 6 hours to build and submit this

   The AI kept the plan's defaults (listed in PLAN.md section 2) and built in the commit order
   from PLAN.md section 10. It started building without waiting for the 4 decisions it had asked
   to have confirmed (see the mistakes table below).

4. Review. I asked the AI to answer 45 questions about its own work, in plain language
   ([WALKTHROUGH.md](WALKTHROUGH.md)). I then had a second Claude session review those answers
   and give fix instructions. The key one:

   > Verdict rule. Using your backtest script, test at least 3 candidate rules [...] Pick the rule
   > using 2025, then report how it does on 2024 as a check. Target: roughly 75 to 85% of weeks
   > "normal" and under 5% "very unusual", across all 7 cities. [...] wait for my OK before
   > changing code.

   The AI tested 10 rules, recommended one, and waited for approval before changing code. The
   results are in [DECISIONS.md](DECISIONS.md), under "Verdict backtest".

5. Code review. I asked the AI to review the finished work as an interviewer would, and to check
   every step. It ran its own checks and had a separate agent read every file for bugs:
   - a fresh clone and cold install
   - 18 edge-case requests
   - a 10-request load test
   - the mobile layout
   - a privacy scan

   The review findings, and what happened to each, are listed below under "Review findings".
   Each fix came with a test that failed before the fix and passes after.

6. Second code review. I asked for the same review again after the fixes. It checked that each
   fix worked, looked for anything the fixes broke, and checked every number in the docs
   against the code. Its findings are under "Second review findings" below.

## How the AI's output was checked

The docs warn that "AI invents parameters", so every upstream assumption was tested with a real
request before it went into the plan or the code:

- Geocoding, forecast, and archive calls, including bad dates, bad latitude, and too many forecast days.
- A throwaway script ran the anomaly math on real Denver data before any code was written. Its
  numbers matched the finished endpoint exactly.
- Every route was tested live (curl and the browser) and with mocked upstream failures in pytest.
- After the build, a backtest (`scripts/backtest_verdict.py`) ran the verdict rule on 357 real
  past weeks. That is what showed the first rule flagged far too many ordinary weeks.

## What the checks caught

These were found by testing. The docs don't mention them, and the AI would not have known them
in advance.

| Finding | What changed |
|---|---|
| The archive silently turns `2025-02-29` into `2025-03-01` rather than failing | Feb 29 is handled in code (`dates.shift_years`), with tests |
| Forecast and archive come from different models and snap to different grid points | Measured on the same past days, 30 to 90 days back: they agree within about 2°F on average (-2.2 to +0.9°F across 7 cities), but can differ by up to about 4°F on single days. Added as a known limit and a page footnote. |
| An archive call once returned HTTP 200 with an empty body | Empty bodies are retried once, with a test |
| Upstream error text can be wrong (`forecast_days=17` says "Given 16") | Upstream text is logged, never shown to users |
| Geocoding returns no `results` key both for no match and for 1-character queries | Treated as an empty list; the API needs 2+ characters |

## Where the AI's first version was wrong or changed

- **The week verdict rule.** The first rule counted a day as unusual if its high or its low was
  outside the 10th to 90th percentile, and called a week "somewhat unusual" at 2 such days. The
  backtest showed it called about 3 in 4 ordinary 2025 weeks unusual. It was replaced, after testing
  10 rules, with separate verdicts for days and nights (highs only and lows only, 5th to 95th
  percentile, 3 or more flagged days). That rule calls 80 to 86% of weeks normal.
- **Denver's warm nights.** The live run said Denver's nights are very unusual (forecast lows 11
  to 23°F above normal). We checked whether the gap between forecast and history caused it. It
  didn't: that gap averages under 1°F for Denver. So the warm nights are in the forecast itself.
- **Chart tooltip.** The first tooltip said the same thing twice ("100% ... 100th pct."), so it
  was simplified.
- **Retry.** The first error state retried only one of the two requests; it now retries both.
- **Trend line.** Planned as a stretch goal, then cut. With 10 years it would mostly be noise.

## Mistakes the AI made, and how they were caught

| Mistake | How it was caught | Fixed? |
|---|---|---|
| **It started building before I confirmed the 4 decisions it had asked about.** I had written "only have the next 6 hours to build and submit this"; it read that as permission to build with its own defaults. | My review afterward | The defaults are documented as the AI's choice. The main one (the verdict rule) was later replaced after a backtest and my approval. |
| Its planning script crashed on an empty upstream reply | The crash | Yes: the client retries empty bodies |
| The first frontend build check never ran (`timeout` doesn't exist on macOS), and the scaffold was committed without it | The error output. Every later build passed. | Yes |
| The first verdict rule over-flagged ordinary weeks | A backtest on 357 past weeks | Yes, replaced (see above) |
| Its first forecast-vs-history check compared the last 2 weeks, where the archive may still be filled with model data, so the numbers it wrote into the docs (0.5°F Denver, 3°F Chicago) were weak | Sydney and Mumbai matched to exactly 0.0°F, which was suspicious | Yes: remeasured on older days, and the docs were corrected |
| It wrote in AI_NOTES that I had "chosen the defaults", which I hadn't | Its own review | Yes (commit `d4bf757`) |
| It warned me that my git email and GitHub login were two different accounts. They are one account (`BhagyeshVaze`); `gh` still shows an old username. | Checking `gh api user` | Yes |
| The README said "Node 20+", but Vite 7 needs Node 20.19+ or 22.12+ | Checking Vite's requirements | Yes; now Node 22.12+, see the second review |
| PLAN.md said the chart's dots would differ in shape; they differ in fill and size only | Writing the walkthrough | Noted, not changed |

## Review findings

From the AI's own review of the finished work (see "Key prompts", step 5).

| # | Severity | Finding | Outcome |
|---|---|---|---|
| 1 | Medium | A thin baseline was reported as "normal". At 5 years with 1 year failing, every day had 28 samples (under 30), so every day was unknown, yet the verdict said "normal". | Fixed: "not enough history" when fewer than 5 of 7 days can be judged. 6 tests. |
| 2 | Medium | In the city search, pressing Enter during the 300 ms debounce picked a stale, hidden result ("Portland, Maine" picked Portland, Oregon). | Fixed: the keyboard only acts on the visible list. Frontend test. |
| 3 | Low | Odd upstream replies (an empty forecast, a null column, a list-shaped reply, float ids) crashed with a 500. | Fixed: 502, or treated as missing data. 6 tests. |
| 4 | Low | A week with Feb 29 counts Feb 28 twice in past years. | Known issue, in the README |
| 5 | Low | A dot at the very edge of the chart band can disagree with its flag. | Listed as a known issue at first; fixed in the second review (it turned out to be common, see below) |
| 6 | Low | "Upstream calls" can say 0 on a first load when two requests share one fetch. | Known issue, in the README |
| 7 | Low | Picking a city fired a wasted search for its full label. | Fixed. Frontend test. |
| 8 | Low | The city search's highlighted option isn't announced to screen readers. | Known issue, in the README |
| 9 | Low | One test assertion accepted every possible value, so it could never fail. | Fixed. A deliberately planted bug passed the old assertion and fails the new one. |
| 10 | Low | On phones, a chart legend swatch wraps away from its label. | Known issue, in the README |
| 11 | Low | A 500 response has no CORS header (no effect through the dev proxy). | Known issue, in the README |

Also from the review:
- The first build took 14 minutes of commit time, so I should be ready to explain every part
  of the code myself.
- The walkthrough file showed a local path containing my username. It now uses a relative path.

## Second review findings

After the first round of fixes. The AI checked each fix, looked for new bugs, and compared every
number in the docs with the code.

| # | Severity | Finding | Outcome |
|---|---|---|---|
| 1 | Medium | The first fix's commit message claimed odd upstream replies would "never" give a 500. Other shapes still did: a bad date, text where a number belongs, a non-text timezone. | Fixed: every date and reading is now checked. 15 tests (13 failed before). The old commit message still overstates; this note corrects it. |
| 2 | Medium | The chart band and the flags disagreed. The band used interpolated percentile lines; the flags used rank. About 11% of dots drawn outside the band (22% at 5 years) were still "normal". The README's description of this known issue was backwards. | Fixed: flags, band, and shown percentile now use the same lines. A 3,000-case test (73 mismatches before, 0 after). Backtest rerun: (a5) still meets the target. |
| 3 | Low | If the forecast itself was missing values, the banner still said "not enough past data, try more years". | Fixed: the banner names the real cause. Backend and frontend tests. |
| 4 | Low | At 5 years, one failed year always gives "not enough history", because 4 years is only 28 values per day. | Kept by design (it was asked for explicitly). Now documented. |
| 5 | Low | The city search got stuck if a picked label was typed again. My fix for the wasted search caused it. | Fixed. Frontend test. |
| 6 | Low | For one render after the query changed, old results were still in state. | Fixed defensively. No test: a single render can't be triggered reliably. |
| 7 | Low | The same-week chart's "past average" line and its sentence could use different years. | Fixed: the backend sends the average it used. Test. |
| 8 | Low | Upstream places with NaN, out-of-range, or true/false coordinates got through. | Fixed. Tests. |
| 9 | Low | Small leftovers: "of 7" hard-coded, the backtest hid a category, no Node `engines` field, logs not ignored. | Fixed |
| 10 | Low | `npm install` printed "2 moderate severity vulnerabilities" from Vitest 3, a dev-only advisory. | Fixed: Vitest 5, 0 vulnerabilities. Vitest 5 needs Node 22.12+, now declared. |
| 11 | Low | Stale docs: "no frontend tests", "about 10 calls" (it's 11), a missing commit row, a wrong file count, and PLAN.md's change list. | Fixed |

Mistakes the AI made in this round:
- It pinned Vitest 3 without checking for advisories.
- A test helper shared one list between tests, so one test's change leaked into later ones. It
  showed up as two unexplained failures, and was fixed.
- It first wrote a test for finding 5 that passed even without the fix. It was removed, because
  it didn't test the bug.
