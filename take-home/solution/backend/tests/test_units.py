from app import units


def test_temperature_value_gets_plus_32():
    assert units.temp(0, "imperial") == 32.0
    assert units.temp(21.7, "imperial") == 71.1


def test_temperature_delta_does_not_get_plus_32():
    assert units.temp_delta(5, "imperial") == 9.0
    assert units.temp_delta(-2.5, "imperial") == -4.5


def test_metric_is_unchanged():
    assert units.temp(21.66, "metric") == 21.7
    assert units.temp_delta(3.04, "metric") == 3.0


def test_rain_mm_to_inches():
    assert units.rain(25.4, "imperial") == 1.0
    assert units.rain(12.34, "metric") == 12.3


def test_none_passes_through():
    assert units.temp(None, "imperial") is None
    assert units.temp_delta(None, "imperial") is None
    assert units.rain(None, "imperial") is None
