"""Backtest week-verdict rules on real past weeks (DECISIONS.md, "Verdict backtest").

Each week of the test year is judged the way the app judges a forecast week, but with the
observed weather in place of a forecast, against the 10 years before it. There is no forecast
involved, so this measures how often a rule flags ordinary weeks. Some weeks were genuinely
unusual, so "not normal" here is not the same as a false alarm.

Run from backend/ with its virtual env active:

    python ../scripts/backtest_verdict.py

The first run downloads 12 years of daily data for 7 cities (about 2,200 of Open-Meteo's
10,000 daily calls) into scripts/.cache/, spaced out to stay under 600 calls a minute.
Later runs use the cache and make no calls.
"""

import json
import os
import statistics as st
import sys
import time
from collections import Counter
from datetime import date, timedelta

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))

from app import anomaly  # noqa: E402  (the app's own math)
from app.dates import shift_years  # noqa: E402
from app.openmeteo import DAILY_VARS, parse_daily  # noqa: E402

CACHE = os.path.join(HERE, ".cache")
YEARS = 10
TEST_YEARS = (2025, 2024)  # rule picked on 2025, checked on 2024
CITIES = {
    "Denver": (39.74, -104.98), "Chicago": (41.85, -87.65), "Miami": (25.77, -80.19),
    "London": (51.51, -0.13), "Tokyo": (35.69, 139.69), "Sydney": (-33.87, 151.21),
    "Mumbai": (19.07, 72.88),
}


def load_history(name: str, lat: float, lon: float) -> dict:
    path = os.path.join(CACHE, f"{name}.json")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        params = {"latitude": lat, "longitude": lon, "daily": DAILY_VARS, "timezone": "auto",
                  "start_date": "2013-12-15", "end_date": "2025-12-31"}
        for attempt in range(3):
            resp = httpx.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=60)
            if resp.status_code == 200 and resp.content.strip():
                with open(path, "w") as f:
                    f.write(resp.text)
                break
            print(f"  {name}: HTTP {resp.status_code}, retrying", file=sys.stderr)
            time.sleep(15)
        else:
            raise SystemExit(f"could not download {name}")
        time.sleep(40)  # one 12-year request weighs about 300 calls
    with open(path) as f:
        return parse_daily(json.load(f))


# --- building blocks ---------------------------------------------------------

def flagged(days: list[dict], var: str, lo: float, hi: float) -> int:
    return sum(d[var]["pct_rank"] is not None and not lo <= d[var]["pct_rank"] <= hi for d in days)


def by_count(n: int, normal_max: int, somewhat_max: int) -> str:
    return "normal" if n <= normal_max else "somewhat" if n <= somewhat_max else "very"


def either_flagged(days: list[dict], lo: float, hi: float) -> int:
    return sum(any(d[v]["pct_rank"] is not None and not lo <= d[v]["pct_rank"] <= hi
                   for v in ("high", "low")) for d in days)


def week_means(week: list[date], hist: dict, var: str) -> list[tuple[int, float]]:
    """(years back, 7-day mean) for each past year, shifted -3..+3 days: 70 samples at 10 years."""
    out = []
    for y in range(1, YEARS + 1):
        for off in range(-3, 4):
            vals = [hist.get(shift_years(d, y) + timedelta(days=off), {}).get(var) for d in week]
            if None not in vals:
                out.append((y, st.fmean(vals)))
    return out


def mean_pct(week: list[date], hist: dict, var: str, detrend: bool = False) -> float:
    samples = week_means(week, hist, var)
    values = [v for _, v in samples]
    if detrend:  # move each past year up to "now" along a trend line fitted to these 10 years
        slope = st.linear_regression([-y for y, _ in samples], values).slope
        values = [v + slope * y for (y, _), v in zip(samples, values)]
    return anomaly.pct_rank(st.fmean(hist[d][var] for d in week), values)


def band(p: float, lo_s: float, hi_s: float, lo_v: float, hi_v: float) -> str:
    if not lo_v <= p <= hi_v:
        return "very"
    if not lo_s <= p <= hi_s:
        return "somewhat"
    return "normal"


def worst(*levels: str) -> str:
    return "very" if "very" in levels else "somewhat" if "somewhat" in levels else "normal"


SHIPPED = {"normal": "normal", "somewhat_unusual": "somewhat", "very_unusual": "very",
           "not_enough_history": "no history"}

RULES = {
    "old: high or low, p10-90, 0-1 / 2-4 / 5-7 days":
        lambda days, w, h: by_count(either_flagged(days, 10, 90), 1, 4),
    "(a) highs only, p10-90, 0-2 / 3-4 / 5-7":
        lambda days, w, h: by_count(flagged(days, "high", 10, 90), 2, 4),
    "(b) high or low, p5-95, 0-1 / 2-4 / 5-7":
        lambda days, w, h: by_count(either_flagged(days, 5, 95), 1, 4),
    "(b2) high or low, p5-95, 0-2 / 3-4 / 5-7":
        lambda days, w, h: by_count(either_flagged(days, 5, 95), 2, 4),
    "(c) week-average high, p10-90 / p2-98":
        lambda days, w, h: band(mean_pct(w, h, "high"), 10, 90, 2, 98),
    "(c2) week-average high or low, p5-95 / p1-99":
        lambda days, w, h: worst(band(mean_pct(w, h, "high"), 5, 95, 1, 99),
                                 band(mean_pct(w, h, "low"), 5, 95, 1, 99)),
    "(c3) week-average high or low, p10-90 / p2-98":
        lambda days, w, h: worst(band(mean_pct(w, h, "high"), 10, 90, 2, 98),
                                 band(mean_pct(w, h, "low"), 10, 90, 2, 98)),
    "(c5) week-average high, p5-95 / p1-99":
        lambda days, w, h: band(mean_pct(w, h, "high"), 5, 95, 1, 99),
    "(cD) as (c), 10-year trend removed":
        lambda days, w, h: band(mean_pct(w, h, "high", detrend=True), 10, 90, 2, 98),
    "(a5) highs only, p5-95, 0-2 / 3-4 / 5-7":
        lambda days, w, h: by_count(flagged(days, "high", 5, 95), 2, 4),
    "(a5) lows only, p5-95, 0-2 / 3-4 / 5-7":
        lambda days, w, h: by_count(flagged(days, "low", 5, 95), 2, 4),
    "shipped code: highs (summarize_week)":
        lambda days, w, h: SHIPPED[anomaly.summarize_week(days)["highs"]["verdict"]],
    "shipped code: lows (summarize_week)":
        lambda days, w, h: SHIPPED[anomaly.summarize_week(days)["lows"]["verdict"]],
}


def weeks_of(year: int):
    start = date(year, 1, 1)
    while start + timedelta(days=6) <= date(year, 12, 24):
        yield [start + timedelta(days=k) for k in range(7)]
        start += timedelta(days=7)


def main() -> None:
    data = {name: load_history(name, *coords) for name, coords in CITIES.items()}
    for year in TEST_YEARS:
        totals = {r: Counter() for r in RULES}
        per_city = {r: {} for r in RULES}
        warm = cool = n_weeks = 0
        mid = []
        for name, hist in data.items():
            for week in weeks_of(year):
                days = anomaly.compare_days({d: hist[d] for d in week}, hist, list(range(1, YEARS + 1)))
                for rule, fn in RULES.items():
                    v = fn(days, week, hist)
                    totals[rule][v] += 1
                    per_city[rule].setdefault(name, Counter())[v] += 1
                p = mean_pct(week, hist, "high")
                mid.append(p)
                warm += p > 90
                cool += p < 10
                n_weeks += 1

        print(f"\n### {year}: {n_weeks} weeks (7 cities x {n_weeks // len(CITIES)})\n")
        print("| Rule | Normal | Somewhat | Very | No history | Normal, by city | Worst city, very |")
        print("|---|---:|---:|---:|---:|---|---:|")
        for rule, c in totals.items():
            n = sum(c.values())
            norm = [pc["normal"] / sum(pc.values()) for pc in per_city[rule].values()]
            very = [pc["very"] / sum(pc.values()) for pc in per_city[rule].values()]
            print(f"| {rule} | {c['normal'] / n:.0%} | {c['somewhat'] / n:.0%} | {c['very'] / n:.0%} "
                  f"| {c['no history'] / n:.0%} "
                  f"| {min(norm):.0%} to {max(norm):.0%} | {max(very):.0%} |")
        print(f"\nWarming check: the median week sits at percentile {st.median(mid):.0f} of the "
              f"10 years before it (50 means no shift). {warm / n_weeks:.0%} of weeks are above the "
              f"90th and {cool / n_weeks:.0%} below the 10th (10% each expected with no shift).")


if __name__ == "__main__":
    main()
