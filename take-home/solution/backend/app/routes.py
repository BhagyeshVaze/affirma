import asyncio
import math
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from . import anomaly
from . import units as u
from .dates import history_window, shift_years
from .errors import ApiError, CityNotFound, InsufficientHistory, InvalidInput, UpstreamRateLimited
from .models import AnomalyResponse, CitySearchResponse, ErrorResponse, SameWeekResponse
from .openmeteo import Meter, OpenMeteo

# Proceed without a failed past year only if enough years are left (PLAN.md section 5)
MIN_YEARS = 3
MIN_YEARS_SHARE = 0.7

ERRORS = {s: {"model": ErrorResponse} for s in (404, 422, 502, 503, 504)}

router = APIRouter(prefix="/api", responses=ERRORS)


def get_client(request: Request) -> OpenMeteo:
    return request.app.state.openmeteo


Client = Annotated[OpenMeteo, Depends(get_client)]


class WeatherQuery:
    """Query params shared by both weather endpoints."""

    def __init__(
        self,
        city: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
        lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
        lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
        years: Annotated[int, Query(ge=5, le=30)] = 10,
        units: u.Units = "imperial",
    ):
        self.city = city.strip() if city is not None else None
        self.lat, self.lon, self.years, self.units = lat, lon, years, units


# --- helpers -----------------------------------------------------------------

def _as_int(value) -> int | None:
    """Upstream sometimes sends numbers as floats or strings; keep only whole numbers."""
    if isinstance(value, bool):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return int(f) if math.isfinite(f) and f.is_integer() else None


def _as_text(value) -> str | None:
    return value if isinstance(value, str) and value else None


def _coordinate(value, limit: float) -> float | None:
    """A real, finite number within plus or minus `limit`, or None."""
    if isinstance(value, bool):
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) and -limit <= f <= limit else None


def clean_place(raw: dict) -> dict | None:
    lat, lon = _coordinate(raw.get("latitude"), 90), _coordinate(raw.get("longitude"), 180)
    if lat is None or lon is None:
        return None
    if not _as_text(raw.get("name")):
        return None
    name, admin1, country = (_as_text(raw.get(k)) for k in ("name", "admin1", "country"))
    parts = []
    for part in (name, admin1, country):
        if part and part not in parts:
            parts.append(part)
    return {
        "id": _as_int(raw.get("id")), "label": ", ".join(parts), "name": name,
        "admin1": admin1, "country": country,
        "country_code": _as_text(raw.get("country_code")), "latitude": lat, "longitude": lon,
        "timezone": _as_text(raw.get("timezone")), "population": _as_int(raw.get("population")),
    }


async def resolve_location(q: WeatherQuery, om: OpenMeteo, meter: Meter) -> dict:
    has_coords = q.lat is not None or q.lon is not None
    if q.city is not None and has_coords:
        raise InvalidInput("Send either city, or lat and lon, not both.")
    if q.city is not None:
        if len(q.city) < 2:
            raise InvalidInput("city: must be at least 2 characters.")
        places = [p for p in map(clean_place, await om.search(q.city, 1, meter)) if p]
        if not places:
            raise CityNotFound(f"No place matches '{q.city}'.")
        p = places[0]
        return {"name": p["label"], "latitude": round(p["latitude"], 2), "longitude": round(p["longitude"], 2)}
    if q.lat is None or q.lon is None:
        raise InvalidInput("Send city, or both lat and lon.")
    return {"name": None, "latitude": round(q.lat, 2), "longitude": round(q.lon, 2)}


async def load_week(om: OpenMeteo, loc: dict, years: int, meter: Meter) -> dict:
    """Forecast for the next 7 local days plus the same window in each past year."""
    lat, lon = loc["latitude"], loc["longitude"]
    forecast = await om.forecast(lat, lon, meter)
    days = forecast["days"]
    week = sorted(days)  # the city's local today plus 6 (PLAN.md gotcha 9)

    offsets = list(range(1, years + 1))
    results = await asyncio.gather(
        *(om.archive(lat, lon, *history_window(week[0], week[-1], y, anomaly.WINDOW_DAYS), meter)
          for y in offsets),
        return_exceptions=True,
    )

    history, used, warnings, failures = {}, [], [], []
    for y, result in zip(offsets, results):
        if isinstance(result, UpstreamRateLimited):
            raise result
        if isinstance(result, ApiError):
            failures.append(result)
            warnings.append(f"History for {week[0].year - y} could not be loaded and was left out.")
            continue
        if isinstance(result, BaseException):
            raise result
        history.update(result)
        used.append(y)

    if not used:
        raise failures[0]  # e.g. a timeout: report the real cause
    if len(used) < max(MIN_YEARS, math.ceil(MIN_YEARS_SHARE * years)):
        raise InsufficientHistory(
            f"Only {len(used)} of {years} past years could be loaded. Try again shortly."
        )
    return {"timezone": forecast["timezone"], "days": days, "week": week,
            "history": history, "years_used": used, "warnings": warnings}


def baseline_info(data: dict, years: int) -> dict:
    used, start = data["years_used"], data["week"][0]
    return {
        "years_requested": years, "years_used": len(used),
        "from_year": shift_years(start, max(used)).year, "to_year": shift_years(start, min(used)).year,
        "window_days": anomaly.WINDOW_DAYS,
    }


def convert_comparison(c: dict, units: u.Units) -> dict:
    return {
        **c,
        "forecast": u.temp(c["forecast"], units), "normal": u.temp(c["normal"], units),
        "p5": u.temp(c["p5"], units), "p95": u.temp(c["p95"], units),
        "anomaly": u.temp_delta(c["anomaly"], units),
        "pct_rank": round(c["pct_rank"], 1) if c["pct_rank"] is not None else None,
    }


def meta(meter: Meter) -> dict:
    return {"upstream_calls": meter.calls, "generated_at": datetime.now(timezone.utc)}


# --- routes ------------------------------------------------------------------

@router.get("/cities", response_model=CitySearchResponse)
async def search_cities(
    om: Client,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    count: Annotated[int, Query(ge=1, le=10)] = 5,
):
    """City search for the picker. No match is an empty list, not an error."""
    q = q.strip()
    if len(q) < 2:
        raise InvalidInput("q: must be at least 2 characters.")
    places = [p for p in map(clean_place, await om.search(q, count, Meter())) if p]
    return {"query": q, "results": places}


@router.get("/weather/anomaly", response_model=AnomalyResponse)
async def weather_anomaly(om: Client, q: Annotated[WeatherQuery, Depends()]):
    """This week's forecast against the normal range for the same dates in past years."""
    meter = Meter()
    loc = await resolve_location(q, om, meter)
    data = await load_week(om, loc, q.years, meter)

    days = anomaly.compare_days(data["days"], data["history"], data["years_used"])
    summary = anomaly.summarize_week(days)
    rain = anomaly.rain_summary(data["days"], data["history"], data["years_used"])

    return {
        "location": {**loc, "timezone": data["timezone"]},
        "units": u.labels(q.units),
        "baseline": baseline_info(data, q.years),
        "week": {
            "start": data["week"][0], "end": data["week"][-1],
            **summary,
            "avg_high_anomaly": u.temp_delta(summary["avg_high_anomaly"], q.units),
            "avg_low_anomaly": u.temp_delta(summary["avg_low_anomaly"], q.units),
            "rain": {
                **rain,
                "forecast_total": u.rain(rain["forecast_total"], q.units),
                "avg_total": u.rain(rain["avg_total"], q.units),
            },
        },
        "days": [
            {
                "date": d["date"],
                "high": convert_comparison(d["high"], q.units),
                "low": convert_comparison(d["low"], q.units),
                "rain": {"forecast": u.rain(d["rain"]["forecast"], q.units)},
            }
            for d in days
        ],
        "warnings": data["warnings"],
        "meta": meta(meter),
    }


@router.get("/weather/same-week", response_model=SameWeekResponse)
async def weather_same_week(om: Client, q: Annotated[WeatherQuery, Depends()]):
    """This week against the same 7 dates in each past year, with a warmth rank."""
    meter = Meter()
    loc = await resolve_location(q, om, meter)
    data = await load_week(om, loc, q.years, meter)
    rows, this_week = anomaly.same_week_years(data["days"], data["history"], data["years_used"])

    return {
        "location": {**loc, "timezone": data["timezone"]},
        "units": u.labels(q.units),
        "baseline": baseline_info(data, q.years),
        "week": {"start": data["week"][0], "end": data["week"][-1]},
        "years": [
            {**r, "avg_high": u.temp(r["avg_high"], q.units), "avg_low": u.temp(r["avg_low"], q.units),
             "total_rain": u.rain(r["total_rain"], q.units)}
            for r in rows
        ],
        "this_week": {**this_week, "vs_past_mean": u.temp_delta(this_week["vs_past_mean"], q.units),
                      "past_avg_high": u.temp(this_week["past_avg_high"], q.units)},
        "warnings": data["warnings"],
        "meta": meta(meter),
    }
