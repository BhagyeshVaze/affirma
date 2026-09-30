from datetime import date

import pytest

from app.errors import UpstreamError
from app.openmeteo import parse_daily


def test_parallel_arrays_become_rows():
    payload = {"daily": {
        "time": ["2026-09-30", "2026-10-01"],
        "temperature_2m_max": [21.7, None],
        "temperature_2m_min": [11.2, 11.1],
        "precipitation_sum": [0.0, 1.5],
    }}
    assert parse_daily(payload) == {
        date(2026, 9, 30): {"high": 21.7, "low": 11.2, "rain": 0.0},
        date(2026, 10, 1): {"high": None, "low": 11.1, "rain": 1.5},
    }


def test_missing_variable_becomes_none():
    payload = {"daily": {"time": ["2026-09-30"], "temperature_2m_max": [20.0]}}
    assert parse_daily(payload)[date(2026, 9, 30)] == {"high": 20.0, "low": None, "rain": None}


@pytest.mark.parametrize("payload", [
    {}, {"daily": None}, {"daily": {"time": "x"}},
    {"daily": {"time": ["2026-09-30"], "temperature_2m_max": [1.0, 2.0]}},
])
def test_bad_shapes_raise_upstream_error(payload):
    with pytest.raises(UpstreamError):
        parse_daily(payload)


def test_explicit_null_column_is_treated_as_missing():
    """Review bug 3: `"temperature_2m_max": null` used to crash with TypeError (a 500)."""
    payload = {"daily": {"time": ["2026-09-30"], "temperature_2m_max": None,
                         "temperature_2m_min": [10.0], "precipitation_sum": [0.0]}}
    assert parse_daily(payload)[date(2026, 9, 30)] == {"high": None, "low": 10.0, "rain": 0.0}


def test_non_list_column_is_upstream_error():
    # a 1-character string has the same length as 1 date, so only a type check catches it
    payload = {"daily": {"time": ["2026-09-30"], "temperature_2m_max": "7"}}
    with pytest.raises(UpstreamError):
        parse_daily(payload)
