"""Anomaly math (PLAN.md section 4). Pure functions, no I/O, metric in and metric out.

`history` everywhere is {date: {"high", "low", "rain"}} merged from the archive windows.
`years_back` is the list of past-year offsets that loaded (1 = last year).
"""

import bisect
import statistics
from datetime import date, timedelta

from .dates import shift_years

# Decisions from PLAN.md section 2, in one place
# The day band and week thresholds were picked by backtest (scripts/backtest_verdict.py,
# DECISIONS.md): about 83% of ordinary weeks come out "normal" and about 3% "very unusual".
WINDOW_DAYS = 3            # plus or minus days around each date
MIN_SAMPLES = 30           # fewer baseline values than this -> level "unknown"
UNUSUAL_PCT = 5            # outside the 5th to 95th percentile
VERY_UNUSUAL_PCT = 2       # outside the 2nd to 98th percentile
SOMEWHAT_UNUSUAL_DAYS = 3  # week verdict: 0-2 flagged days normal, 3-4 somewhat, 5-7 very
VERY_UNUSUAL_DAYS = 5
MIN_DAYS_FOR_RANK = 6      # a past week needs 6 of 7 days of data to be ranked
MIN_DAYS_FOR_VERDICT = 5   # fewer judgeable days than this -> "not_enough_history"

TEMP_VARS = ("high", "low")
FLAGGED = ("unusual", "very_unusual")


def baseline_samples(
    day: date, var: str, history: dict, years_back: list[int], window_days: int = WINDOW_DAYS
) -> list[float]:
    """Values of `var` on the same date plus or minus `window_days`, over every past year."""
    samples = []
    for y in years_back:
        center = shift_years(day, y)
        for offset in range(-window_days, window_days + 1):
            value = history.get(center + timedelta(days=offset), {}).get(var)
            if value is not None:
                samples.append(value)
    return samples


def pct_rank(value: float, samples: list[float]) -> float:
    """Where `value` sits on the same scale as statistics.quantiles(method="inclusive"):
    0 at the smallest sample, 100 at the largest, straight lines in between. Using one scale
    for the band, the flag, and the shown percentile keeps the three in agreement.
    A value equal to several samples gets the middle of their positions.
    """
    s = sorted(samples)
    n = len(s)
    if n == 1:
        return 50.0
    lo, hi = bisect.bisect_left(s, value), bisect.bisect_right(s, value)
    if lo < hi:  # ties
        position = (lo + hi - 1) / 2
    elif lo == 0:
        position = 0.0
    elif lo == n:
        position = n - 1.0
    else:
        position = (lo - 1) + (value - s[lo - 1]) / (s[lo] - s[lo - 1])
    return 100 * position / (n - 1)


def classify(value: float, cuts: dict) -> str:
    """Level from where the value sits against the percentile lines (the chart's band)."""
    if value < cuts["p2"] or value > cuts["p98"]:
        return "very_unusual"
    if value < cuts["p5"] or value > cuts["p95"]:
        return "unusual"
    return "normal"


def percentile_lines(samples: list[float]) -> dict:
    """The flag lines: p5/p95 (unusual) and p2/p98 (very unusual), from the constants above."""
    q = statistics.quantiles(samples, n=100, method="inclusive")  # q[k - 1] is the kth percentile
    return {
        "p2": q[VERY_UNUSUAL_PCT - 1], "p5": q[UNUSUAL_PCT - 1],
        "p95": q[99 - UNUSUAL_PCT], "p98": q[99 - VERY_UNUSUAL_PCT],
    }


def compare(forecast: float | None, samples: list[float]) -> dict:
    """Compare one forecast value with its baseline samples."""
    result = {
        "forecast": forecast, "normal": None, "p5": None, "p95": None, "anomaly": None,
        "pct_rank": None, "level": "unknown", "direction": None, "n": len(samples),
    }
    if len(samples) < MIN_SAMPLES:
        return result
    cuts = percentile_lines(samples)
    result.update(normal=statistics.fmean(samples), p5=cuts["p5"], p95=cuts["p95"])
    if forecast is None:
        return result
    anomaly = forecast - result["normal"]
    direction = "warmer" if anomaly > 0 else "cooler" if anomaly < 0 else "same"
    result.update(anomaly=anomaly, pct_rank=pct_rank(forecast, samples),
                  level=classify(forecast, cuts), direction=direction)
    return result


def compare_days(forecast_days: dict, history: dict, years_back: list[int]) -> list[dict]:
    """One comparison per forecast day, for the high and the low."""
    return [
        {
            "date": day,
            **{
                var: compare(values.get(var), baseline_samples(day, var, history, years_back))
                for var in TEMP_VARS
            },
            "rain": {"forecast": values.get("rain")},
        }
        for day, values in sorted(forecast_days.items())
    ]


def _mean(values) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.fmean(values) if values else None


def verdict_for(days: list[dict], var: str) -> dict:
    """Week verdict for one variable (highs or lows), from its flagged days only.

    Days that can't be judged (too little history, or no forecast value) are "unknown". If
    fewer than 5 of 7 days can be judged, the verdict is "not_enough_history", never "normal".
    """
    unusual = sum(d[var]["level"] in FLAGGED for d in days)
    very = sum(d[var]["level"] == "very_unusual" for d in days)
    known = sum(d[var]["level"] != "unknown" for d in days)
    # why a day can't be judged matters to the reader: no forecast vs thin history
    no_forecast = sum(d[var]["level"] == "unknown" and d[var].get("forecast") is None for d in days)
    if known < MIN_DAYS_FOR_VERDICT:
        verdict = "not_enough_history"
    elif unusual >= VERY_UNUSUAL_DAYS:
        verdict = "very_unusual"
    elif unusual >= SOMEWHAT_UNUSUAL_DAYS:
        verdict = "somewhat_unusual"
    else:
        verdict = "normal"
    return {"unusual_days": unusual, "very_unusual_days": very, "days_judged": known,
            "days_without_forecast": no_forecast, "verdict": verdict}


def summarize_week(days: list[dict]) -> dict:
    """Separate verdicts for highs (days) and lows (nights). They are never combined:
    counting a day when either was flagged made about 3 in 4 ordinary weeks "unusual"."""
    return {
        "avg_high_anomaly": _mean(d["high"]["anomaly"] for d in days),
        "avg_low_anomaly": _mean(d["low"]["anomaly"] for d in days),
        "highs": verdict_for(days, "high"),
        "lows": verdict_for(days, "low"),
    }


def week_totals(rows: list[dict | None]) -> dict:
    """Average high and low, and total rain, for one 7-day week. Missing days are skipped."""
    rows = [r or {} for r in rows]
    rains = [r.get("rain") for r in rows]
    return {
        "avg_high": _mean(r.get("high") for r in rows),
        "avg_low": _mean(r.get("low") for r in rows),
        # a total with missing days would look drier than it was, so require all 7
        "total_rain": sum(rains) if all(v is not None for v in rains) else None,
        "days_with_data": sum(r.get("high") is not None for r in rows),
    }


def rain_summary(forecast_days: dict, history: dict, years_back: list[int]) -> dict:
    """Rain is mostly zeros, so compare weekly totals only (PLAN.md gotcha 16)."""
    week = sorted(forecast_days)
    forecast_total = week_totals([forecast_days[d] for d in week])["total_rain"]
    past = [
        week_totals([history.get(shift_years(d, y)) for d in week])["total_rain"]
        for y in years_back
    ]
    past = [t for t in past if t is not None]
    comparable = forecast_total is not None
    return {
        "forecast_total": forecast_total,
        "avg_total": _mean(past),
        "years_wetter": sum(t > forecast_total for t in past) if comparable else 0,
        "years_drier": sum(t < forecast_total for t in past) if comparable else 0,
        "years_compared": len(past) if comparable else 0,
    }


def same_week_years(forecast_days: dict, history: dict, years_back: list[int]) -> tuple[list, dict]:
    """This week and the same 7 dates in each past year, oldest first, plus this week's rank."""
    week = sorted(forecast_days)
    rows = []
    for y in sorted(years_back, reverse=True):
        dates = [shift_years(d, y) for d in week]
        rows.append({
            "year": dates[0].year, "start": dates[0], "end": dates[-1],
            **week_totals([history.get(d) for d in dates]), "is_forecast": False,
        })
    rows.append({
        "year": week[0].year, "start": week[0], "end": week[-1],
        **week_totals([forecast_days[d] for d in week]), "is_forecast": True,
    })

    ranked = [r for r in rows if r["days_with_data"] >= MIN_DAYS_FOR_RANK]
    ranked.sort(key=lambda r: r["avg_high"], reverse=True)
    rank = next((i + 1 for i, r in enumerate(ranked) if r["is_forecast"]), None)
    this_high = rows[-1]["avg_high"]
    past_mean = _mean(r["avg_high"] for r in ranked if not r["is_forecast"])
    this_week = {
        "rank_warmest": rank,
        "out_of": len(ranked),
        "vs_past_mean": this_high - past_mean if this_high is not None and past_mean is not None else None,
    }
    return rows, this_week
