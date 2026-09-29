# Frankfurter

Daily exchange rates from the European Central Bank, back to 1999.

| | |
|---|---|
| Docs | [frankfurter.dev](https://frankfurter.dev/) |
| Auth | None |
| Rate limit | None published. Rates update once per business day, so cache for hours. |
| Format | JSON |
| Version | Use **v1**: simple, 30 currencies, still updated daily |

## Endpoints

Base URL: `https://api.frankfurter.dev/v1`

| Route | Returns |
|---|---|
| `GET /latest` | Latest rates |
| `GET /{YYYY-MM-DD}` | Rates on a date |
| `GET /{start}..{end}` | Daily series between two dates |
| `GET /{start}..` | Daily series up to today |
| `GET /currencies` | Code → name map |

| Param | Example | Notes |
|---|---|---|
| `base` | `USD` | Default `EUR` |
| `symbols` | `EUR,GBP,JPY` | Default: all |
| `amount` | `250` | Default `1` |

## Examples

```bash
curl "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR,GBP,JPY"
curl "https://api.frankfurter.dev/v1/2020-03-16?base=USD"
curl "https://api.frankfurter.dev/v1/2024-01-01..2024-06-30?base=USD&symbols=EUR,GBP"
curl "https://api.frankfurter.dev/v1/latest?amount=100&base=USD&symbols=EUR"
curl "https://api.frankfurter.dev/v1/currencies"
```

## Response

Single date:

```json
{ "amount": 1.0, "base": "USD", "date": "2026-09-29",
  "rates": { "EUR": 0.88067, "GBP": 0.75489, "JPY": 157.12 } }
```

Series, keyed by date. This request asked for `2024-01-01..` but starts on `2023-12-29`:

```json
{
  "amount": 1.0, "base": "USD",
  "start_date": "2023-12-29", "end_date": "2024-06-28",
  "rates": {
    "2023-12-29": { "EUR": 0.90498, "GBP": 0.78647 },
    "2024-01-02": { "EUR": 0.91274, "GBP": 0.79085 }
  }
}
```

## Sample data

What 1 USD bought in 2025:

| Currency | Start | End | Change | Low | High |
|---|---:|---:|---:|---:|---:|
| EUR | 0.96256 | 0.85106 | −11.6% | 0.84481 | 0.98058 |
| GBP | 0.79813 | 0.74264 | −7.0% | 0.72718 | 0.82526 |
| JPY | 156.95 | 156.67 | −0.2% | 140.34 | 158.41 |

## Gotchas

- No data on weekends or holidays. Series have gaps.
- Ranges start on the last business day **on or before** your start date.
- Weekend dates return the previous business day's rates.
- `rates` is keyed by date string. Sort the keys yourself.
- Unknown currency: HTTP 404 `{"message": "not found"}`. Same if `symbols` includes the base.
- **Python's `urllib` gets HTTP 403.** Use `httpx` or `requests`.
- `api.frankfurter.app` redirects here. Use `api.frankfurter.dev` directly.
- Long ranges aren't downsampled. 10 years ≈ 2,500 dates.
- A v2 API exists with more currencies and a different shape. Don't mix versions; values differ slightly.

## Dashboard ideas

### 1. Currency leaderboard
- **Shows:** several currencies on one chart (indexed to 100), ranked by change, volatility, and max drop.
- **Endpoint:** `GET /api/fx/performance?base=USD&symbols=EUR,GBP,JPY&from=2025-01-01&to=2025-12-31`
- **Backend:** pivot to one series per currency, index to 100, compute daily returns, volatility, drawdown.

### 2. Trip budget
- **Shows:** what a budget is worth in 2–4 currencies today vs 30, 90, and 365 days ago.
- **Endpoint:** `GET /api/fx/budget?home=USD&amount=2000&destinations=EUR,JPY,MXN`
- **Backend:** one year-long series, find the nearest business day for each lookback, compute values and changes.

### 3. Moving averages
- **Shows:** one pair with 7- and 30-day averages, crossover points, and 52-week high and low.
- **Endpoint:** `GET /api/fx/trend?base=EUR&quote=USD&days=365`
- **Backend:** rolling averages over business days, crossover detection, range position.

### 4. Cross-rate grid
- **Shows:** a currency × currency grid of % changes over a period.
- **Endpoint:** `GET /api/fx/matrix?symbols=USD,EUR,GBP,JPY,CHF&from=..&to=..`
- **Backend:** one single-base series, derive each pair as `rate_B / rate_A`, compute changes. No extra calls.
