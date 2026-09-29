# Jolpica F1: Formula 1 Results

Open-source Formula 1 data from 1950 to the current season: schedules, results,
qualifying, standings, laps, and pit stops. It's a drop-in replacement for the retired **Ergast** API,
so most Ergast tutorials work if you swap the host.

- **Official docs:** https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md
- **Rate limits:** https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md
  (unauthenticated: 4 requests/second burst, 500 requests/hour sustained. The maintainers say these
  limits **will decrease** in future, and going over returns HTTP 429.)
- **Auth:** none
- **Format:** JSON

Base URL: `https://api.jolpi.ca/ergast/f1`

## Sample data

Real data from this API:

| Driver | After round 6 | After round 12 | After round 18 | Final (round 24) |
|---|---:|---:|---:|---:|
| Norris | 115 | 226 | 314 | 423 |
| Verstappen | 99 | 165 | 273 | 421 |
| Piastri | 131 | 234 | 336 | 410 |

*Built from all pages of `2025/results.json` plus `2025/sprint.json` (7 requests), summed per driver per round. Leave out the sprints and every total is wrong: Norris would end on 394, not 423. This is the kind of data idea 1 (Title race progression) is built on.*

## Endpoints

`{season}` is a year like `2025`, or `current`. `{round}` is a round number, or `last`.
`current` is the **in-progress** season (2026 at the time of writing), so its data changes after every race.
For a stable, complete dataset, use a finished season such as `2025`.

| Route | Returns |
|-------|---------|
| `/seasons.json` | All seasons |
| `/{season}.json` | Race schedule (calendar) |
| `/{season}/{round}.json` | One race's info |
| `/{season}/results.json` | Race results for the whole season (**paginated**) |
| `/{season}/{round}/results.json` | Results for one race |
| `/{season}/{round}/qualifying.json` | Qualifying results (`Q1`/`Q2`/`Q3` times; drivers knocked out early have no `Q2`/`Q3` key) |
| `/{season}/{round}/sprint.json` | Sprint results |
| `/{season}/driverStandings.json` | Championship standings (latest) |
| `/{season}/{round}/driverStandings.json` | Standings **after** that round |
| `/{season}/constructorStandings.json` | Team standings |
| `/{season}/drivers.json`, `/{season}/constructors.json` | Entrants |
| `/{season}/circuits.json` | Circuits used that season |
| `/{season}/{round}/laps.json` | Lap-by-lap positions and times (**large, paginated**) |
| `/{season}/{round}/pitstops.json` | Pit stops |
| `/{season}/status.json` | Finishing status counts (see the Gotchas section for how these differ by era) |

**Filters** can be chained, for example:
- `/2025/drivers/max_verstappen/results.json`: one driver's results in 2025
- `/2025/constructors/ferrari/results.json`: one team's results

Standings routes **require a season**. `/drivers/hamilton/driverStandings.json` returns HTTP 400
(`{"detail": "Bad Request: Missing one of the required parameters ['season_year']."}`).

**Pagination:** `?limit=100&offset=0`. The maximum `limit` is 100. The response includes `total`.

## Example requests

```bash
curl "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"
curl "https://api.jolpi.ca/ergast/f1/2025/5/results.json"
curl "https://api.jolpi.ca/ergast/f1/2025/results.json?limit=100&offset=100"
curl "https://api.jolpi.ca/ergast/f1/current/last/results.json"
```

## Response shapes (trimmed)

Every response is wrapped in `MRData`:

```json
{
  "MRData": {
    "limit": "30", "offset": "0", "total": "20",
    "RaceTable": {
      "season": "2025",
      "Races": [
        {
          "season": "2025", "round": "5", "raceName": "Saudi Arabian Grand Prix", "date": "2025-04-20",
          "Circuit": { "circuitId": "jeddah", "circuitName": "Jeddah Corniche Circuit",
                       "Location": { "lat": "21.6319", "long": "39.1044", "locality": "Jeddah", "country": "Saudi Arabia" } },
          "Results": [
            { "position": "1", "points": "25", "grid": "2", "laps": "50", "status": "Finished",
              "Driver": { "driverId": "piastri", "code": "PIA", "givenName": "Oscar", "familyName": "Piastri", "nationality": "Australian" },
              "Constructor": { "constructorId": "mclaren", "name": "McLaren" },
              "Time": { "millis": "4866758", "time": "1:21:06.758" },
              "FastestLap": { "rank": "3", "lap": "50", "Time": { "time": "1:32.228" } } }
          ]
        }
      ]
    }
  }
}
```

Standings:

```json
{ "MRData": { "StandingsTable": { "season": "2025", "round": "24",
  "StandingsLists": [ { "season": "2025", "round": "24",
    "DriverStandings": [
      { "position": "1", "points": "423", "wins": "7",
        "Driver": { "driverId": "norris", "code": "NOR", "givenName": "Lando", "familyName": "Norris" },
        "Constructors": [ { "constructorId": "mclaren", "name": "McLaren" } ] }
    ] } ] } } }
```

*(These values are real responses from `2025/5/results.json` and `2025/driverStandings.json`, trimmed.)*

## Gotchas

- **Every number is a string** (`"points": "25"`, `"total": "479"`). Convert them yourself.
- Season-wide `results.json` is paginated by **result rows** (2025 has 479 rows). Pages cut through
  races: `offset=100` returned rounds 6–10 plus **just 1 row of round 11**. Merge rows by round across
  pages instead of assuming each page holds whole races. The default `limit` is 30 and the maximum is 100
  (asking for more silently returns 100).
- Sprint results are separate (`/{season}/sprint.json`, rows under `SprintResults`), and their points
  are **not** in `results.json`. In 2025, Norris has 394 points from races alone but 423 in the
  standings once sprints are added. Sum both for correct totals.
- Standings "after round N" need one request per round. With the 500/hour limit, **cache**
  these, since past seasons never change.
- Not every driver has a `code` or `permanentNumber` (especially historical drivers). Some results have
  no `Time` (DNF), and `positionText` can be `"R"` (retired), `"D"` (disqualified), and so on.
- Finishing `status` detail depends on the era. 2025 has only 5 values (`Finished`, `Lapped`, `Retired`,
  `Disqualified`, `Did not start`), while 2010 has 35 (`+1 Lap`, `Engine`, `Collision`, `Hydraulics`, ...).
- The `.json` suffix is optional. `/2025/5/results/` returns the same JSON.
- Responses are cached upstream (`cache-control: max-age=600`), so very recent races may take a few minutes to appear.

## Dashboard ideas

Pick one of these, or combine parts of them. In each idea, the backend does real work:
it paginates, converts the string numbers, joins results, and builds cumulative statistics.
Just forwarding the `MRData` payload doesn't count.

> **Rate limit reminder:** 4 requests/second and 500/hour. Most of these ideas need one request per
> round, so **cache** in your backend. Past seasons never change and can be cached forever.

### 1. Title race progression
**Dashboard shows:** A season selector, a line chart of each top-N driver's **cumulative points
after every round**, and a standings table with the gap to the leader.

**Example endpoint:** `GET /api/f1/{season}/progression?top=5`

**Backend work:**
- Fetch all race results (paginate, or loop over rounds) **and** sprint results.
- Convert the strings to numbers and sum points per driver per round.
- Build a running total and reshape it into chart-ready series.

### 2. Teammate head-to-head
**Dashboard shows:** A row per team with split bars comparing the two drivers: qualifying head-to-head,
race head-to-head (when both finished), points, and average finishing position.

**Example endpoint:** `GET /api/f1/{season}/teammates`

**Backend work:**
- Join qualifying and race results by round and constructor.
- Pair teammates and compare them only when both took part.
- Handle mid-season driver swaps and DNFs (explain your rules in `DECISIONS.md`).

### 3. Driver season report
**Dashboard shows:** Pick a driver to see KPI tiles (wins, podiums, DNFs, points per race), a bar chart of
positions gained or lost per race (grid vs finish), and a breakdown of retirement reasons.

**Example endpoint:** `GET /api/f1/{season}/drivers/{driverId}/report`

**Backend work:**
- Fetch the driver's results. Compute `grid − position` (treat pit-lane starts, `grid = 0`, carefully),
  finish rate, and averages.
- Group `status` values into Finished, Lapped, Retired, Disqualified, and Did not start. Note that
  recent seasons only say `Retired`, not *why* (see Gotchas).

### 4. Constructor dominance over the years
**Dashboard shows:** A stacked area chart of each team's share of total points (or wins) per season across
a chosen span (e.g. the last 10 seasons), and the most dominant season for each team.

**Example endpoint:** `GET /api/f1/constructors/dominance?from=2014&to=2025`

**Backend work:**
- Fetch the final constructor standings for each season (one call per season, and cache them).
- Compute the percentage share of points per team per season and normalize team names and IDs across years.
