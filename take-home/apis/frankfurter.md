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
