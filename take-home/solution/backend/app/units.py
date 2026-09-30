"""Unit conversion. All math runs in °C and mm; conversion happens once, on the way out.

Values (a temperature) and deltas (an anomaly, a difference) convert differently:
a delta scales by 1.8 but gets no +32.
"""

from typing import Literal

Units = Literal["imperial", "metric"]


def temp(c: float | None, units: Units) -> float | None:
    if c is None:
        return None
    return round(c * 1.8 + 32 if units == "imperial" else c, 1)


def temp_delta(c: float | None, units: Units) -> float | None:
    if c is None:
        return None
    return round(c * 1.8 if units == "imperial" else c, 1)


def rain(mm: float | None, units: Units) -> float | None:
    if mm is None:
        return None
    return round(mm / 25.4, 2) if units == "imperial" else round(mm, 1)


def labels(units: Units) -> dict[str, str]:
    if units == "imperial":
        return {"temperature": "°F", "precipitation": "in"}
    return {"temperature": "°C", "precipitation": "mm"}
