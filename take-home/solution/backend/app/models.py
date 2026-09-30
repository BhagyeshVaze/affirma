"""Response shapes (PLAN.md section 4). They also drive the OpenAPI docs at /docs."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

Level = Literal["normal", "unusual", "very_unusual", "unknown"]


class Place(BaseModel):
    id: int | None
    label: str
    name: str
    admin1: str | None
    country: str | None
    country_code: str | None
    latitude: float
    longitude: float
    timezone: str | None
    population: int | None


class CitySearchResponse(BaseModel):
    query: str
    results: list[Place]


class Location(BaseModel):
    name: str | None
    latitude: float
    longitude: float
    timezone: str | None


class UnitLabels(BaseModel):
    temperature: str
    precipitation: str


class Meta(BaseModel):
    upstream_calls: int
    generated_at: datetime


class Baseline(BaseModel):
    years_requested: int
    years_used: int
    from_year: int
    to_year: int
    window_days: int


class Comparison(BaseModel):
    forecast: float | None
    normal: float | None
    p5: float | None
    p95: float | None
    anomaly: float | None
    pct_rank: float | None
    level: Level
    direction: Literal["warmer", "cooler", "same"] | None
    n: int


class DayRain(BaseModel):
    forecast: float | None


class Day(BaseModel):
    date: date
    high: Comparison
    low: Comparison
    rain: DayRain


class RainSummary(BaseModel):
    forecast_total: float | None
    avg_total: float | None
    years_wetter: int
    years_drier: int
    years_compared: int


class Verdict(BaseModel):
    unusual_days: int
    very_unusual_days: int
    days_judged: int
    days_without_forecast: int
    verdict: Literal["normal", "somewhat_unusual", "very_unusual", "not_enough_history"]


class WeekSummary(BaseModel):
    start: date
    end: date
    avg_high_anomaly: float | None
    avg_low_anomaly: float | None
    highs: Verdict
    lows: Verdict
    rain: RainSummary


class AnomalyResponse(BaseModel):
    location: Location
    units: UnitLabels
    baseline: Baseline
    week: WeekSummary
    days: list[Day]
    warnings: list[str]
    meta: Meta


class WeekRange(BaseModel):
    start: date
    end: date


class YearRow(BaseModel):
    year: int
    start: date
    end: date
    avg_high: float | None
    avg_low: float | None
    total_rain: float | None
    days_with_data: int
    is_forecast: bool


class ThisWeek(BaseModel):
    rank_warmest: int | None
    out_of: int
    vs_past_mean: float | None


class SameWeekResponse(BaseModel):
    location: Location
    units: UnitLabels
    baseline: Baseline
    week: WeekRange
    years: list[YearRow]
    this_week: ThisWeek
    warnings: list[str]
    meta: Meta


class ErrorBody(BaseModel):
    code: str
    message: str
    retry_after_s: int | None


class ErrorResponse(BaseModel):
    error: ErrorBody
