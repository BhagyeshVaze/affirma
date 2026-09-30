from datetime import date

from app.dates import history_window, shift_years


def test_shift_normal_date():
    assert shift_years(date(2026, 9, 30), 1) == date(2025, 9, 30)


def test_feb_29_becomes_feb_28_in_non_leap_year():
    assert shift_years(date(2028, 2, 29), 1) == date(2027, 2, 28)


def test_feb_29_stays_in_leap_year():
    assert shift_years(date(2028, 2, 29), 4) == date(2024, 2, 29)


def test_window_is_13_days_so_it_costs_one_call():
    start, end = history_window(date(2026, 9, 30), date(2026, 10, 6), 1, 3)
    assert (start, end) == (date(2025, 9, 27), date(2025, 10, 9))
    assert (end - start).days + 1 == 13


def test_week_crossing_new_year_stays_contiguous():
    start, end = history_window(date(2026, 12, 29), date(2027, 1, 4), 1, 3)
    assert (start, end) == (date(2025, 12, 26), date(2026, 1, 7))
