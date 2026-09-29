# CoinGecko (Keyless Public API): Crypto Prices

Market data for thousands of cryptocurrencies. CoinGecko offers a **keyless** public
tier. Don't send any API key header.

- **Official docs:** https://docs.coingecko.com/docs/keyless-public-api and
  https://docs.coingecko.com/reference/introduction
- **Auth:** none. Don't send `x-cg-demo-api-key` or `x-cg-pro-api-key`.
- **Rate limits:** **low and variable** (roughly a handful of calls per minute). Expect
  HTTP **429** if you exceed it. **Caching is mandatory for this API.**
- **Format:** JSON

Base URL: `https://api.coingecko.com/api/v3`

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /ping` | Health check |
| `GET /simple/price` | Current price for one or more coins |
| `GET /coins/markets` | Ranked list with price, market cap, volume, % change |
| `GET /coins/list` | Every coin `{id, symbol, name}`, which is a large response. Fetch once and cache. |
| `GET /coins/{id}` | Full coin detail (heavy; use flags to trim) |
| `GET /coins/{id}/market_chart` | Historical prices, market caps and volumes |
| `GET /coins/{id}/ohlc` | Open/high/low/close candles |
| `GET /search?query=eth` | Search coins by name or symbol |
| `GET /search/trending` | Trending coins |
| `GET /global` | Total market cap, BTC dominance, and more |

### Key parameters

| Endpoint | Params |
|----------|--------|
| `/simple/price` | `ids=bitcoin,ethereum` (required), `vs_currencies=usd,eur` (required), `include_market_cap`, `include_24hr_vol`, `include_24hr_change`, `include_last_updated_at` (`true`/`false`) |
| `/coins/markets` | `vs_currency=usd` (required), `ids`, `order=market_cap_desc`, `per_page` (1–250), `page`, `sparkline=true`, `price_change_percentage=1h,24h,7d,30d` |
| `/coins/{id}/market_chart` | `vs_currency=usd` (required), `days=1\|7\|30\|90\|365` (required), `interval=daily` (optional) |
| `/coins/{id}/ohlc` | `vs_currency=usd`, `days=1\|7\|14\|30\|90\|180\|365` |
| `/coins/{id}` | `localization=false&tickers=false&community_data=false&developer_data=false` to trim it |

## Example requests

```bash
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
curl "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=20&price_change_percentage=24h,7d"
curl "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"
```

## Response shapes (trimmed)

`/simple/price`:

```json
{ "bitcoin": { "usd": 63512.12, "usd_24h_change": -1.84 },
  "ethereum": { "usd": 2451.03, "usd_24h_change": 0.52 } }
```

`/coins/markets`:

```json
[
  { "id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "image": "https://...",
    "current_price": 63512.12, "market_cap": 1250000000000, "market_cap_rank": 1,
    "total_volume": 28000000000, "high_24h": 64200, "low_24h": 62900,
    "price_change_percentage_24h": -1.84, "circulating_supply": 19700000,
    "ath": 73738, "ath_change_percentage": -13.9, "last_updated": "2026-09-29T14:00:00.000Z" }
]
```

`/coins/{id}/market_chart` returns arrays of `[timestamp_ms, value]` pairs:

```json
{
  "prices":        [[1788000000000, 61234.5], [1788003600000, 61301.2]],
  "market_caps":   [[1788000000000, 1.21e12], [1788003600000, 1.22e12]],
  "total_volumes": [[1788000000000, 2.5e10],  [1788003600000, 2.6e10]]
}
```

`/coins/{id}/ohlc`: `[[timestamp_ms, open, high, low, close], ...]`

## Gotchas

- Use the coin **`id`** (e.g. `bitcoin`, `ethereum`, `solana`), not the ticker symbol.
  Symbols aren't unique.
- `market_chart` picks the granularity automatically: `days=1` gives ~5-minute points,
  2–90 days gives hourly, and more than 90 days gives daily. Use `interval=daily` to force daily points.
- The free and keyless tiers may only return up to the **last 365 days** of history.
- On a 429, back off and serve cached data. Don't retry in a tight loop.
- Don't call this API from the frontend. Your backend should cache, for example for 60+
  seconds for prices and hours for historical data.
