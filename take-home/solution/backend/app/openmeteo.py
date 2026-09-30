"""Open-Meteo client: timeouts, one retry, 429 handling, call budget, and caching."""

import asyncio
import logging
from datetime import date

import httpx

from . import config
from .cache import AsyncTTLCache, CallBudget
from .errors import UpstreamError, UpstreamRateLimited, UpstreamTimeout

log = logging.getLogger(__name__)

# Open-Meteo field name -> our name
DAILY_FIELDS = {
    "temperature_2m_max": "high",
    "temperature_2m_min": "low",
    "precipitation_sum": "rain",
}
DAILY_VARS = ",".join(DAILY_FIELDS)

# {date: {"high": °C | None, "low": °C | None, "rain": mm | None}}
Daily = dict[date, dict[str, float | None]]


class Meter:
    """Counts real upstream calls made for one API request (reported in `meta`)."""

    def __init__(self) -> None:
        self.calls = 0


def parse_daily(payload: dict) -> Daily:
    """Turn Open-Meteo's parallel arrays into one row per date."""
    daily = payload.get("daily")
    if not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
        raise UpstreamError("Weather service sent data in an unexpected shape.")
    times = daily["time"]
    columns = {}
    for api_name, our_name in DAILY_FIELDS.items():
        values = daily.get(api_name, [None] * len(times))
        if len(values) != len(times):
            raise UpstreamError("Weather service sent data in an unexpected shape.")
        columns[our_name] = values
    return {
        date.fromisoformat(t): {name: values[i] for name, values in columns.items()}
        for i, t in enumerate(times)
    }


def _retry_after(resp: httpx.Response) -> int:
    try:
        return max(1, int(resp.headers.get("Retry-After", "")))
    except ValueError:
        return config.DEFAULT_RETRY_AFTER_S


class OpenMeteo:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http
        self.limit = asyncio.Semaphore(config.MAX_CONCURRENT_UPSTREAM)
        self.budget = CallBudget(config.UPSTREAM_BUDGET_PER_MIN)
        self.geocode_cache = AsyncTTLCache(config.GEOCODE_TTL_S, config.CACHE_MAX_ENTRIES)
        self.forecast_cache = AsyncTTLCache(config.FORECAST_TTL_S, config.CACHE_MAX_ENTRIES)
        self.archive_cache = AsyncTTLCache(config.ARCHIVE_TTL_S, config.CACHE_MAX_ENTRIES)

    async def _get_json(self, url: str, params: dict, meter: Meter) -> dict:
        """GET with one retry on timeouts, network errors, 5xx, and empty bodies.

        400 and 429 are never retried. Upstream error text is logged, not shown to users,
        because some of it is wrong (PLAN.md gotcha 5).
        """
        for attempt in (1, 2):
            last = attempt == 2
            self.budget.take()
            meter.calls += 1
            try:
                async with self.limit:
                    resp = await self.http.get(url, params=params)
            except httpx.TimeoutException:
                if last:
                    raise UpstreamTimeout("The weather service took too long to answer.")
                await asyncio.sleep(config.RETRY_DELAY_S)
                continue
            except httpx.TransportError as exc:
                if last:
                    raise UpstreamError("Could not reach the weather service.") from exc
                await asyncio.sleep(config.RETRY_DELAY_S)
                continue

            if resp.status_code == 429:
                wait = _retry_after(resp)
                raise UpstreamRateLimited(
                    f"The weather service is busy. Try again in {wait} s.", retry_after_s=wait
                )
            if resp.status_code >= 500 or not resp.content.strip():
                # an empty 200 body happened once while planning (PLAN.md gotcha 6)
                if last:
                    raise UpstreamError("The weather service sent an empty or failed response.")
                await asyncio.sleep(config.RETRY_DELAY_S)
                continue
            if resp.status_code != 200:
                log.warning("Open-Meteo %s -> %s: %s", url, resp.status_code, resp.text[:300])
                raise UpstreamError("The weather service rejected the request.")
            try:
                payload = resp.json()
            except ValueError:
                if last:
                    raise UpstreamError("The weather service sent a response we could not read.")
                await asyncio.sleep(config.RETRY_DELAY_S)
                continue
            if isinstance(payload, dict) and payload.get("error"):
                log.warning("Open-Meteo %s error body: %s", url, payload.get("reason"))
                raise UpstreamError("The weather service rejected the request.")
            return payload
        raise AssertionError("unreachable")

    async def search(self, name: str, count: int, meter: Meter) -> list[dict]:
        name = name.strip()
        params = {"name": name, "count": count, "language": "en", "format": "json"}

        async def fetch():
            payload = await self._get_json(config.GEOCODING_URL, params, meter)
            # no `results` key at all when nothing matches (PLAN.md gotcha 3)
            return payload.get("results", [])

        return await self.geocode_cache.get((name.lower(), count), fetch)

    async def forecast(self, lat: float, lon: float, meter: Meter) -> dict:
        """Next 7 days in the city's local time: {"timezone": str, "days": Daily}."""
        lat, lon = round(lat, 2), round(lon, 2)
        params = {
            "latitude": lat, "longitude": lon, "daily": DAILY_VARS,
            "timezone": "auto", "forecast_days": 7,
        }

        async def fetch():
            payload = await self._get_json(config.FORECAST_URL, params, meter)
            return {"timezone": payload.get("timezone"), "days": parse_daily(payload)}

        return await self.forecast_cache.get((lat, lon), fetch)

    async def archive(self, lat: float, lon: float, start: date, end: date, meter: Meter) -> Daily:
        lat, lon = round(lat, 2), round(lon, 2)
        params = {
            "latitude": lat, "longitude": lon, "daily": DAILY_VARS, "timezone": "auto",
            "start_date": start.isoformat(), "end_date": end.isoformat(),
        }

        async def fetch():
            return parse_daily(await self._get_json(config.ARCHIVE_URL, params, meter))

        return await self.archive_cache.get((lat, lon, start, end), fetch)
