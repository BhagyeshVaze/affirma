from datetime import date, timedelta


def shift_years(d: date, years_back: int) -> date:
    """The same calendar date `years_back` years earlier.

    Feb 29 becomes Feb 28 in non-leap years. We must do this ourselves: the archive API
    silently turns 2025-02-29 into 2025-03-01 instead of failing (PLAN.md gotcha 1).
    Shifting by an offset, not setting a year, also keeps weeks that cross Jan 1 intact.
    """
    try:
        return d.replace(year=d.year - years_back)
    except ValueError:
        return d.replace(year=d.year - years_back, day=28)


def history_window(start: date, end: date, years_back: int, pad_days: int) -> tuple[date, date]:
    """Date range to fetch for one past year: the shifted week plus `pad_days` on each side."""
    return (
        shift_years(start, years_back) - timedelta(days=pad_days),
        shift_years(end, years_back) + timedelta(days=pad_days),
    )
