from datetime import date, timedelta

import pytest

from app import anomaly
from app.anomaly import (
    baseline_samples, classify, compare, pct_rank, rain_summary, same_week_years, summarize_week,
)
from app.dates import shift_years

WEEK = [date(2026, 9, 30) + timedelta(days=i) for i in range(7)]


def make_history(years: int, value_for=lambda d, y: 20.0, rain=0.0) -> dict:
    """History covering each past year's window, with a value chosen per date."""
    history = {}
    for y in range(1, years + 1):
        start = shift_years(WEEK[0], y) - timedelta(days=3)
        for i in range(13):
            d = start + timedelta(days=i)
            v = value_for(d, y)
            history[d] = {"high": v, "low": v - 10, "rain": rain}
    return history


# --- pct_rank and classify ---------------------------------------------------

def test_pct_rank_counts_ties_as_half():
    assert pct_rank(5, [1, 5, 5, 9]) == 50.0
    assert pct_rank(10, [1, 2, 3, 4]) == 100.0
    assert pct_rank(0, [1, 2, 3, 4]) == 0.0


@pytest.mark.parametrize("pct, level", [
    (1.9, "very_unusual"), (2, "unusual"), (4.9, "unusual"), (5, "normal"),
    (50, "normal"), (95, "normal"), (95.1, "unusual"), (98, "unusual"), (98.1, "very_unusual"),
])
def test_classify_boundaries(pct, level):
    assert classify(pct) == level


# --- baseline_samples --------------------------------------------------------

def test_baseline_has_7_samples_per_year():
    history = make_history(10)
    assert len(baseline_samples(WEEK[0], "high", history, list(range(1, 11)))) == 70


def test_baseline_skips_nulls_and_missing_years():
    history = make_history(10)
    history[shift_years(WEEK[0], 1)]["high"] = None
    samples = baseline_samples(WEEK[0], "high", history, [1, 2])
    assert len(samples) == 13


# --- compare -----------------------------------------------------------------

def test_compare_normal_day():
    samples = [float(v) for v in range(100)]  # 0..99
    r = compare(50.0, samples)
    assert r["normal"] == pytest.approx(49.5)
    assert r["p5"] == pytest.approx(4.95)
    assert r["p95"] == pytest.approx(94.05)
    assert r["anomaly"] == pytest.approx(0.5)
    assert r["pct_rank"] == pytest.approx(50.5)
    assert r["level"] == "normal"
    assert r["direction"] == "warmer"


def test_compare_record_warm_day_is_very_unusual():
    r = compare(200.0, [float(v) for v in range(100)])
    assert r["level"] == "very_unusual"
    assert r["pct_rank"] == 100.0


def test_compare_too_few_samples_is_unknown():
    r = compare(20.0, [20.0] * (anomaly.MIN_SAMPLES - 1))
    assert r["level"] == "unknown"
    assert r["normal"] is None


def test_compare_missing_forecast_keeps_baseline():
    r = compare(None, [float(v) for v in range(100)])
    assert r["level"] == "unknown"
    assert r["normal"] == pytest.approx(49.5)
    assert r["anomaly"] is None


# --- summarize_week ----------------------------------------------------------

def day(high_level: str, low_level: str = "normal", anomaly_value: float = 1.0) -> dict:
    return {"high": {"level": high_level, "anomaly": anomaly_value},
            "low": {"level": low_level, "anomaly": anomaly_value}}


@pytest.mark.parametrize("flagged, verdict", [
    (0, "normal"), (2, "normal"), (3, "somewhat_unusual"), (4, "somewhat_unusual"),
    (5, "very_unusual"), (7, "very_unusual"),
])
def test_week_verdict_thresholds(flagged, verdict):
    days = [day("unusual") for _ in range(flagged)] + [day("normal") for _ in range(7 - flagged)]
    assert summarize_week(days)["highs"]["verdict"] == verdict


def test_highs_and_lows_get_separate_verdicts_never_combined():
    # 3 days with an unusual high only, 3 other days with an unusual low only
    days = [day("unusual", "normal")] * 3 + [day("normal", "unusual")] * 3 + [day("normal")]
    s = summarize_week(days)
    assert s["highs"] == {"unusual_days": 3, "very_unusual_days": 0, "days_with_history": 7,
                          "verdict": "somewhat_unusual"}
    assert s["lows"] == {"unusual_days": 3, "very_unusual_days": 0, "days_with_history": 7,
                         "verdict": "somewhat_unusual"}


def test_very_unusual_days_count_as_flagged_and_are_reported():
    s = summarize_week([day("very_unusual")] * 5 + [day("normal")] * 2)
    assert s["highs"]["verdict"] == "very_unusual"
    assert s["highs"]["very_unusual_days"] == 5
    assert s["lows"]["verdict"] == "normal"


def test_unknown_days_do_not_count_and_null_anomalies_are_skipped():
    days = [{"high": {"level": "unknown", "anomaly": None}, "low": {"level": "unknown", "anomaly": None}}] * 7
    s = summarize_week(days)
    assert s["highs"]["unusual_days"] == 0
    assert s["highs"]["verdict"] == "not_enough_history"
    assert s["avg_high_anomaly"] is None


# --- rain_summary ------------------------------------------------------------

def test_rain_compares_weekly_totals():
    history = make_history(4, rain=1.0)   # every past week: 7 mm
    forecast = {d: {"high": 20, "low": 10, "rain": 0.5} for d in WEEK}  # 3.5 mm
    r = rain_summary(forecast, history, [1, 2, 3, 4])
    assert r["forecast_total"] == pytest.approx(3.5)
    assert r["avg_total"] == pytest.approx(7.0)
    assert (r["years_wetter"], r["years_drier"], r["years_compared"]) == (4, 0, 4)


def test_rain_skips_past_weeks_with_missing_days():
    history = make_history(2, rain=1.0)
    history[shift_years(WEEK[3], 1)]["rain"] = None
    forecast = {d: {"high": 20, "low": 10, "rain": 0.0} for d in WEEK}
    assert rain_summary(forecast, history, [1, 2])["years_compared"] == 1


# --- same_week_years ---------------------------------------------------------

def test_same_week_ranks_this_week_among_past_years():
    # past year y has highs of 20 - y, so last year was warmest (19)
    history = make_history(5, value_for=lambda d, y: 20.0 - y)
    forecast = {d: {"high": 18.5, "low": 8.5, "rain": 0.0} for d in WEEK}
    rows, this_week = same_week_years(forecast, history, [1, 2, 3, 4, 5])
    assert [r["year"] for r in rows] == [2021, 2022, 2023, 2024, 2025, 2026]
    assert rows[-1]["is_forecast"] is True
    assert this_week["rank_warmest"] == 2          # behind only 2025 (19.0)
    assert this_week["out_of"] == 6
    assert this_week["vs_past_mean"] == pytest.approx(18.5 - 17.0)


def test_same_week_leaves_incomplete_years_out_of_rank():
    history = make_history(3)
    for d in WEEK[:2]:
        history[shift_years(d, 1)]["high"] = None
    forecast = {d: {"high": 20, "low": 10, "rain": 0.0} for d in WEEK}
    rows, this_week = same_week_years(forecast, history, [1, 2, 3])
    assert rows[2]["days_with_data"] == 5
    assert this_week["out_of"] == 3


# --- not enough history (review bug 1) ----------------------------------------

def unknown_day() -> dict:
    return {"level": "unknown", "anomaly": None}


@pytest.mark.parametrize("known, verdict", [
    (0, "not_enough_history"), (4, "not_enough_history"), (5, "normal"), (7, "normal"),
])
def test_verdict_needs_5_of_7_days_with_enough_history(known, verdict):
    days = [day("normal")] * known + [{"high": unknown_day(), "low": unknown_day()}] * (7 - known)
    s = summarize_week(days)
    assert s["highs"]["verdict"] == verdict
    assert s["lows"]["verdict"] == verdict
    assert s["highs"]["days_with_history"] == known


def test_thin_history_beats_flagged_days():
    # 4 flagged days would be "somewhat unusual", but only 4 of 7 days can be judged at all
    days = [day("unusual")] * 4 + [{"high": unknown_day(), "low": unknown_day()}] * 3
    assert summarize_week(days)["highs"]["verdict"] == "not_enough_history"
