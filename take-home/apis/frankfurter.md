# Frankfurter: Currency Exchange Rates

Open-source exchange-rate API based on reference rates from the European Central Bank
and other central banks.

- **Official docs:** https://frankfurter.dev/
- **Source code:** https://github.com/lineofflight/frankfurter
- **Auth:** none
- **Rate limits:** no hard limit for reasonable use. Rates change once per business day, so cache for hours.
- **Format:** JSON

There are two versions on the same host:

- **v1** (`https://api.frankfurter.dev/v1`) is frozen but kept available. It's simple and has about 30 major currencies from the ECB. **We recommend v1 for this exercise.**
- **v2** (`https://api.frankfurter.dev/v2`) blends many central-bank providers and covers more currencies. See the official docs if you want to use it.

> The older host `api.frankfurter.app` may still work, but use `api.frankfurter.dev`.

## v1 endpoints

| Route | Purpose |
|-------|---------|
| `GET /v1/latest` | Most recent rates |
| `GET /v1/{YYYY-MM-DD}` | Rates on a given date (weekend or holiday → previous business day) |
| `GET /v1/{start}..{end}` | Time series between two dates, e.g. `2024-01-01..2024-06-30` |
| `GET /v1/{start}..` | Time series from a date until today |
| `GET /v1/currencies` | Map of currency code → name |

Query parameters (all optional):

| Param | Example | Notes |
|-------|---------|-------|
| `base` | `USD` | Default `EUR`. `from` is an accepted alias. |
| `symbols` | `EUR,GBP,JPY` | Limit the target currencies. `to` is an accepted alias. |
| `amount` | `250` | Converts this amount instead of 1 |

## Example requests

```bash
curl "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,GBP,JPY"
curl "https://api.frankfurter.dev/v1/2020-03-16?base=USD"
curl "https://api.frankfurter.dev/v1/2024-01-01..2024-06-30?base=USD&symbols=EUR,GBP"
curl "https://api.frankfurter.dev/v1/latest?amount=100&base=USD&symbols=EUR"
curl "https://api.frankfurter.dev/v1/currencies"
```

## Response shapes

Latest or single date:

```json
{ "amount": 1.0, "base": "USD", "date": "2026-09-28",
  "rates": { "EUR": 0.9123, "GBP": 0.7811, "JPY": 147.52 } }
```

Time series (keyed by date):

```json
{
  "amount": 1.0, "base": "USD",
  "start_date": "2024-01-02", "end_date": "2024-06-28",
  "rates": {
    "2024-01-02": { "EUR": 0.9106, "GBP": 0.7869 },
    "2024-01-03": { "EUR": 0.9145, "GBP": 0.7903 }
  }
}
```

Currencies:

```json
{ "AUD": "Australian Dollar", "BRL": "Brazilian Real", "EUR": "Euro", "USD": "United States Dollar" }
```

## v2 at a glance (optional)

Endpoints that appear in the v2 docs include `GET /v2/rates?base=USD&quotes=EUR,GBP`,
`GET /v2/rate/{base}/{quote}`, `GET /v2/providers/ecb/rates?date=YYYY-MM-DD`,
and `GET /v2/coverage`. The shapes differ from v1, so read https://frankfurter.dev/ before using it.

## Gotchas

- Rates are published **once per business day** (around 16:00 CET). There's no data for weekends
  or holidays, so a time series skips those dates. Account for gaps when computing
  "daily" returns or charting.
- `start_date` in a response may be later than the date you asked for, because it snaps to a business day.
- The time-series `rates` object is keyed by date string. Sort the keys before charting.
  Don't rely on object key order.
- Rates are *reference* rates, not live trading prices.
- An unknown currency code returns HTTP 404 or 422 with `{ "message": "not found" }`.

## Dashboard ideas

Pick one of these, or combine parts of them. In each idea, the backend does real work:
it reshapes the date-keyed time series and computes financial statistics. Just returning
the raw rates doesn't count.

### 1. Currency performance leaderboard
**Dashboard shows:** A date-range picker, a line chart of several currencies **rebased to 100** at the
start date (so they're comparable), and a ranked table of % change, volatility, and max drawdown.

**Example endpoint:** `GET /api/fx/performance?base=USD&symbols=EUR,GBP,JPY,CAD&from=2025-01-01&to=2025-12-31`

**Backend work:**
- Turn the `{date: {cur: rate}}` object into sorted per-currency series.
- Rebase each series to 100 at the start date.
- Compute total % change, daily returns, volatility (standard deviation of daily returns), best and
  worst day, and max drawdown.
- Handle the weekend and holiday gaps in the series.

### 2. Trip budget tracker
**Dashboard shows:** The user enters a home currency, an amount, and 2–4 destination currencies. For
each destination, a card shows what the budget is worth today vs 30, 90, and 365 days ago, with a sparkline.

**Example endpoint:** `GET /api/fx/budget?home=USD&amount=2000&destinations=EUR,JPY,MXN`

**Backend work:**
- Fetch one time series covering the last year.
- Pick the nearest available business day for each lookback date, then compute the converted
  amounts and % differences.
- Find the best and worst day in the period to have exchanged the money.

### 3. Trend & moving averages
**Dashboard shows:** One currency pair with 7-day and 30-day moving averages, markers where the
averages cross, and the 52-week high and low, plus where today sits in that range.

**Example endpoint:** `GET /api/fx/trend?base=EUR&quote=USD&days=365`

**Backend work:**
- Compute the rolling averages with correct windows over business days.
- Detect crossovers, compute the 52-week high and low, and express the current rate's position in
  that range as a percentage.

### 4. Cross-rate heatmap
**Dashboard shows:** A matrix of currencies × currencies colored by the % change of each pair over the
chosen period (e.g. how EUR/JPY moved).

**Example endpoint:** `GET /api/fx/matrix?symbols=USD,EUR,GBP,JPY,CHF&from=..&to=..`

**Backend work:**
- Use a **single-base** time series and derive every cross rate yourself
  (rate A→B = rate_B / rate_A), instead of making N² upstream calls.
- Compute the start-to-end % change for every pair.
