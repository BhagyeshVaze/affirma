# Jolpica F1: Formula 1 Results

Open-source Formula 1 data from 1950 to the current season: schedules, results,
qualifying, standings, laps, and pit stops. It's a drop-in replacement for the retired **Ergast** API,
so most Ergast tutorials work if you swap the host.

- **Official docs:** https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md
- **Rate limits:** https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md
  (unauthenticated: ~4 requests/second burst, ~200 requests/hour sustained)
- **Auth:** none
- **Format:** JSON

Base URL: `https://api.jolpi.ca/ergast/f1`

## Endpoints

`{season}` is a year like `2025`, or `current`. `{round}` is a round number, or `last`.

| Route | Returns |
|-------|---------|
| `/seasons.json` | All seasons |
| `/{season}.json` | Race schedule (calendar) |
| `/{season}/{round}.json` | One race's info |
| `/{season}/results.json` | Race results for the whole season (**paginated**) |
| `/{season}/{round}/results.json` | Results for one race |
| `/{season}/{round}/qualifying.json` | Qualifying results (Q1/Q2/Q3 times) |
| `/{season}/{round}/sprint.json` | Sprint results |
| `/{season}/driverStandings.json` | Championship standings (latest) |
| `/{season}/{round}/driverStandings.json` | Standings **after** that round |
| `/{season}/constructorStandings.json` | Team standings |
| `/{season}/drivers.json`, `/{season}/constructors.json` | Entrants |
| `/{season}/circuits.json` | Circuits used that season |
| `/{season}/{round}/laps.json` | Lap-by-lap positions and times (**large, paginated**) |
| `/{season}/{round}/pitstops.json` | Pit stops |
| `/{season}/status.json` | Finishing status counts ("Finished", "+1 Lap", "Engine", ...) |

**Filters** can be chained, for example:
- `/2025/drivers/max_verstappen/results.json`: one driver's results in 2025
- `/2025/constructors/ferrari/results.json`: one team's results
- `/drivers/hamilton/driverStandings/1.json`: seasons in which Hamilton finished 1st

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
    "limit": "30", "offset": "0", "total": "24",
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
              "Time": { "millis": "4866000", "time": "1:21:06.758" },
              "FastestLap": { "rank": "3", "lap": "40", "Time": { "time": "1:31.778" } } }
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

*(The values above are illustrative. Call the API for real numbers.)*

## Gotchas

- **Every number is a string** (`"points": "25"`, `"total": "479"`). Convert them yourself.
- Season-wide `results.json` is paginated by **result rows**. A season has about 20 rows per race,
  so you'll need several pages at `limit=100`. For per-round work, it's often simpler to loop over rounds.
- Standings "after round N" need one request per round. With the ~200/hour limit, **cache**
  these, since past seasons never change.
- Not every driver has a `code` or `permanentNumber` (especially historical drivers). Some results have
  no `Time` (DNF), and `positionText` can be `"R"` (retired), `"D"` (disqualified), and so on.
- The `.json` suffix follows Ergast conventions, and JSON is the default either way.

## Dashboard ideas

Pick one of these, or combine parts of them. In each idea, the backend does real work:
it paginates, converts the string numbers, joins results, and builds cumulative statistics.
Just forwarding the `MRData` payload doesn't count.

> **Rate limit reminder:** ~200 requests/hour. Most of these ideas need one request per
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
- Group `status` values into categories such as Finished, Lapped, Mechanical, and Accident.

### 4. Constructor dominance over the years
**Dashboard shows:** A stacked area chart of each team's share of total points (or wins) per season across
a chosen span (e.g. the last 10 seasons), and the most dominant season for each team.

**Example endpoint:** `GET /api/f1/constructors/dominance?from=2014&to=2025`

**Backend work:**
- Fetch the final constructor standings for each season (one call per season, and cache them).
- Compute the percentage share of points per team per season and normalize team names and IDs across years.
