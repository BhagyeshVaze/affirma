# Jolpica F1

Formula 1 results, qualifying, and standings since 1950. Replaces the retired Ergast API with the same routes.

| | |
|---|---|
| Docs | [Docs](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md) · [Rate limits](https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md) |
| Auth | None |
| Rate limit | 4/second, 500/hour. May drop in future. Over the limit: HTTP 429 |
| Format | JSON |

## Endpoints

Base URL: `https://api.jolpi.ca/ergast/f1`

`{season}` is a year or `current` (the in-progress season). `{round}` is a number or `last`.
Use a finished season, like `2025`, for stable data.

| Route | Returns |
|---|---|
| `/{season}.json` | Race calendar |
| `/{season}/results.json` | All race results (paginated) |
| `/{season}/{round}/results.json` | One race |
| `/{season}/{round}/qualifying.json` | Qualifying (`Q1`, `Q2`, `Q3`) |
| `/{season}/sprint.json` | Sprint results |
| `/{season}/driverStandings.json` | Driver standings |
| `/{season}/{round}/driverStandings.json` | Standings after a round |
| `/{season}/constructorStandings.json` | Team standings |
| `/{season}/drivers.json`, `/{season}/constructors.json` | Entrants |
| `/{season}/{round}/laps.json` | Lap times (large, paginated) |
| `/{season}/{round}/pitstops.json` | Pit stops |
| `/{season}/status.json` | Finish status counts |
| `/seasons.json` | All seasons |

**Filters:** `/2025/drivers/max_verstappen/results.json`, `/2025/constructors/ferrari/results.json`

**Paging:** `?limit=100&offset=0`. Default 30, max 100.

## Examples

```bash
curl "https://api.jolpi.ca/ergast/f1/2025/driverStandings.json"
curl "https://api.jolpi.ca/ergast/f1/2025/5/results.json"
curl "https://api.jolpi.ca/ergast/f1/2025/results.json?limit=100&offset=100"
curl "https://api.jolpi.ca/ergast/f1/current/last/results.json"
```

## Response

Race results:

```json
{
  "MRData": {
    "limit": "30", "offset": "0", "total": "20",
    "RaceTable": {
      "season": "2025",
      "Races": [
        {
          "round": "5", "raceName": "Saudi Arabian Grand Prix", "date": "2025-04-20",
          "Circuit": { "circuitId": "jeddah", "circuitName": "Jeddah Corniche Circuit" },
          "Results": [
            { "position": "1", "points": "25", "grid": "2", "laps": "50", "status": "Finished",
              "Driver": { "driverId": "piastri", "code": "PIA", "givenName": "Oscar", "familyName": "Piastri" },
              "Constructor": { "constructorId": "mclaren", "name": "McLaren" },
              "Time": { "millis": "4866758", "time": "1:21:06.758" } }
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
  "StandingsLists": [ { "DriverStandings": [
      { "position": "1", "points": "423", "wins": "7",
        "Driver": { "driverId": "norris", "code": "NOR" },
        "Constructors": [ { "constructorId": "mclaren", "name": "McLaren" } ] }
  ] } ] } } }
```

## Sample data

2025 cumulative points, races plus sprints:

| Driver | Round 6 | Round 12 | Round 18 | Final |
|---|---:|---:|---:|---:|
| Norris | 115 | 226 | 314 | 423 |
| Verstappen | 99 | 165 | 273 | 421 |
| Piastri | 131 | 234 | 336 | 410 |

## Gotchas

- **All numbers are strings.** Convert them.
- **Sprint points aren't in `results.json`.** Add `sprint.json`. Without sprints, Norris ends on 394, not 423.
- Pages split races. A page can end partway through a race. Merge rows by round.
- Standings routes need a season. `/drivers/hamilton/driverStandings.json` returns HTTP 400.
- Recent seasons only say `Retired`, not why. Older seasons list causes (`Engine`, `Collision`, …).
- Some results have no `Time` (didn't finish). `positionText` can be `R` or `D`.
- Knocked-out drivers have no `Q2` or `Q3`.
- Past seasons never change. Cache them.

## Dashboard ideas

### 1. Title race
- **Shows:** cumulative points per driver after each round, and the gap to the leader.
- **Endpoint:** `GET /api/f1/{season}/progression?top=5`
- **Backend:** fetch all result and sprint pages, convert strings, sum by driver and round, build running totals.

### 2. Teammate battle
- **Shows:** each team's two drivers compared on qualifying, races, and points.
- **Endpoint:** `GET /api/f1/{season}/teammates`
- **Backend:** join qualifying and race results by round and team. Decide how to handle driver swaps and DNFs.

### 3. Driver report
- **Shows:** one driver's wins, podiums, DNFs, positions gained per race, and finish status breakdown.
- **Endpoint:** `GET /api/f1/{season}/drivers/{driverId}/report`
- **Backend:** compute `grid − position` (grid `0` means pit-lane start), finish rate, and averages.

### 4. Team dominance
- **Shows:** each team's share of points per season over 10+ years.
- **Endpoint:** `GET /api/f1/constructors/dominance?from=2014&to=2025`
- **Backend:** one standings call per season (cache them), compute shares, match team IDs across years.
