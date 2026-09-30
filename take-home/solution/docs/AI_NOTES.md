# How AI was used

Tool: Claude (Opus 5.5) in Claude Code. It read the task docs, wrote the plan, and wrote the
code in small commits. I reviewed each step and chose the defaults.

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
   from PLAN.md section 10.

## How the AI's output was checked

The docs warn that "AI invents parameters", so every upstream assumption was tested with a real
request before it went into the plan or the code:

- Geocoding, forecast, and archive calls, including bad dates, bad latitude, and too many forecast days.
- A throwaway script ran the anomaly math on real Denver data before any code was written. Its
  numbers matched the finished endpoint exactly.
- Every route was tested live (curl and the browser) and with mocked upstream failures in pytest.

## What the checks caught

These were found by testing. The docs don't mention them, and the AI would not have known them
in advance.

| Finding | What changed |
|---|---|
| The archive silently turns `2025-02-29` into `2025-03-01` rather than failing | Feb 29 is handled in code (`dates.shift_years`), with tests |
| Forecast and archive snap to different grid points | Measured the offset between them (0.5 to 3°F on the same days) and added it as a known limit and a page footnote |
| An archive call once returned HTTP 200 with an empty body | Empty bodies are retried once, with a test |
| Upstream error text can be wrong (`forecast_days=17` says "Given 16") | Upstream text is logged, never shown to users |
| Geocoding returns no `results` key both for no match and for 1-character queries | Treated as an empty list; the API needs 2+ characters |

## Where the AI's first version was wrong or changed

- **The week verdict.** The plan's example response showed "normal" for Denver. The live run said
  "very unusual" because of the lows: forecast lows ran 11 to 23°F above normal. Before trusting
  it, we checked whether the forecast-vs-history offset caused it. It didn't: that offset is
  only about 0.5°F for Denver. So the warm nights are in the forecast itself.
- **Chart tooltip.** The first tooltip said the same thing twice ("100% ... 100th pct."), so it
  was simplified.
- **Retry.** The first error state retried only one of the two requests; it now retries both.
- **Trend line.** Planned as a stretch goal, then cut. With 10 years it would mostly be noise.
