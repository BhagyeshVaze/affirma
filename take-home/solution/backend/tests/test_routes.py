"""Route tests with Open-Meteo mocked by respx. No real network calls."""

import json
from datetime import date, timedelta

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app import config
from app.main import app

WEEK = [date(2026, 9, 30) + timedelta(days=i) for i in range(7)]
FORECAST_HIGHS = [20.0] * 6 + [35.0]  # last day far above anything in history


def daily(days, highs, lows, rain):
    return {"daily": {
        "time": [d.isoformat() for d in days],
        "temperature_2m_max": highs, "temperature_2m_min": lows, "precipitation_sum": rain,
    }}


def forecast_json():
    # fresh lists every call, so a test that edits one can't leak into the next
    return {"timezone": "America/Denver",
            **daily(WEEK, list(FORECAST_HIGHS), [10.0] * 7, [0.0] * 7)}


def archive_response(request: httpx.Request) -> httpx.Response:
    """Build history for whatever range was asked: highs cycle 17..23 °C, lows 10 below."""
    start = date.fromisoformat(request.url.params["start_date"])
    end = date.fromisoformat(request.url.params["end_date"])
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    highs = [17.0 + d.toordinal() % 7 for d in days]
    return httpx.Response(200, json=daily(days, highs, [h - 10 for h in highs], [1.0] * len(days)))


GEOCODE_DENVER = {"results": [{
    "id": 5419384, "name": "Denver", "latitude": 39.73915, "longitude": -104.9847,
    "country": "United States", "country_code": "US", "admin1": "Colorado",
    "timezone": "America/Denver", "population": 729019,
}]}


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr(config, "RETRY_DELAY_S", 0)


@pytest.fixture
def client():
    with TestClient(app) as c:  # new app state (and empty caches) per test
        yield c


@pytest.fixture
def upstream():
    with respx.mock(assert_all_called=False) as mock:
        mock.forecast = mock.get(config.FORECAST_URL).respond(json=forecast_json())
        mock.archive = mock.get(config.ARCHIVE_URL).mock(side_effect=archive_response)
        mock.geocode = mock.get(config.GEOCODING_URL).respond(json=GEOCODE_DENVER)
        yield mock


ANOMALY = "/api/weather/anomaly?lat=39.74&lon=-104.98"


# --- happy paths -------------------------------------------------------------

def test_anomaly_happy_path(client, upstream):
    r = client.get(ANOMALY)
    assert r.status_code == 200
    body = r.json()
    assert len(body["days"]) == 7
    assert body["baseline"] == {"years_requested": 10, "years_used": 10, "from_year": 2016,
                                "to_year": 2025, "window_days": 3}
    assert body["meta"]["upstream_calls"] == 11  # 1 forecast + 10 archive
    assert body["days"][0]["high"]["n"] == 70
    assert body["days"][0]["high"]["forecast"] == 68.0  # 20 °C in °F
    assert body["days"][6]["high"]["level"] == "very_unusual"
    # 1 flagged high out of 7 is still a normal week; highs and lows are judged separately
    assert body["week"]["highs"] == {"unusual_days": 1, "very_unusual_days": 1,
                                     "days_judged": 7, "days_without_forecast": 0, "verdict": "normal"}
    # forecast lows of 10 °C sit mid-range in the mocked history (7 to 13 °C): 50th percentile
    assert body["week"]["lows"] == {"unusual_days": 0, "very_unusual_days": 0,
                                    "days_judged": 7, "days_without_forecast": 0, "verdict": "normal"}
    assert body["days"][0]["low"]["pct_rank"] == 50.0
    assert set(body["days"][0]["high"]) >= {"p5", "p95"}
    assert body["units"] == {"temperature": "°F", "precipitation": "in"}


def test_second_request_is_served_from_cache(client, upstream):
    client.get(ANOMALY)
    r = client.get(ANOMALY)
    assert r.json()["meta"]["upstream_calls"] == 0
    assert upstream.forecast.call_count == 1


def test_same_week_reuses_the_same_cached_data(client, upstream):
    client.get(ANOMALY)
    r = client.get("/api/weather/same-week?lat=39.74&lon=-104.98")
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["upstream_calls"] == 0
    assert len(body["years"]) == 11
    assert body["years"][-1]["is_forecast"] is True
    assert body["this_week"]["out_of"] == 11


def test_metric_units(client, upstream):
    body = client.get(ANOMALY + "&units=metric").json()
    assert body["days"][0]["high"]["forecast"] == 20.0
    assert body["units"]["temperature"] == "°C"


def test_city_name_is_geocoded_and_label_returned(client, upstream):
    body = client.get("/api/weather/anomaly?city=Denver").json()
    assert body["location"]["name"] == "Denver, Colorado, United States"
    assert body["location"]["latitude"] == 39.74


def test_city_search_cleans_results(client, upstream):
    body = client.get("/api/cities?q=Denver").json()
    assert body["results"][0]["label"] == "Denver, Colorado, United States"


# --- bad input ---------------------------------------------------------------

@pytest.mark.parametrize("query, fragment", [
    ("lat=95&lon=0", "lat"),
    ("lat=10", "Send city, or both lat and lon"),
    ("", "Send city, or both lat and lon"),
    ("city=Denver&lat=1&lon=1", "not both"),
    ("lat=1&lon=1&years=2", "years"),
    ("lat=1&lon=1&units=kelvin", "units"),
    ("lat=abc&lon=1", "lat"),
])
def test_bad_input_is_422_with_our_error_shape(client, upstream, query, fragment):
    r = client.get(f"/api/weather/anomaly?{query}")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_input"
    assert fragment in r.json()["error"]["message"]
    assert upstream.forecast.call_count == 0


def test_short_search_query_is_422(client, upstream):
    r = client.get("/api/cities?q=D")
    assert r.status_code == 422


def test_unknown_city_is_404(client, upstream):
    upstream.geocode.respond(json={"generationtime_ms": 0.4})  # no results key
    r = client.get("/api/weather/anomaly?city=Zzqqxxv")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "city_not_found"


def test_search_with_no_match_is_empty_list(client, upstream):
    upstream.geocode.respond(json={"generationtime_ms": 0.4})
    r = client.get("/api/cities?q=Zzqqxxv")
    assert r.status_code == 200
    assert r.json()["results"] == []


# --- upstream failures -------------------------------------------------------

def test_upstream_429_becomes_503_with_retry_after(client, upstream):
    upstream.forecast.respond(429, headers={"Retry-After": "42"}, json={"error": True})
    r = client.get(ANOMALY)
    assert r.status_code == 503
    assert r.headers["Retry-After"] == "42"
    assert r.json()["error"] == {"code": "upstream_rate_limited",
                                 "message": "The weather service is busy. Try again in 42 s.",
                                 "retry_after_s": 42}
    assert upstream.forecast.call_count == 1  # 429 is not retried


def test_timeout_is_retried_once_then_504(client, upstream):
    upstream.forecast.mock(side_effect=httpx.ConnectTimeout("slow"))
    r = client.get(ANOMALY)
    assert r.status_code == 504
    assert r.json()["error"]["code"] == "upstream_timeout"
    assert upstream.forecast.call_count == 2


def test_empty_body_is_retried_and_recovers(client, upstream):
    upstream.forecast.side_effect = [httpx.Response(200, content=b""),
                                     httpx.Response(200, json=forecast_json())]
    r = client.get(ANOMALY)
    assert r.status_code == 200
    assert upstream.forecast.call_count == 2


def test_upstream_400_is_502_and_hides_upstream_text(client, upstream):
    upstream.forecast.respond(400, json={"error": True, "reason": "Given 16"})
    r = client.get(ANOMALY)
    assert r.status_code == 502
    assert "Given 16" not in r.json()["error"]["message"]


def test_one_missing_year_is_a_warning_not_a_failure(client, upstream):
    def flaky(request):
        if request.url.params["start_date"].startswith("2020"):
            return httpx.Response(500)
        return archive_response(request)
    upstream.archive.mock(side_effect=flaky)
    body = client.get(ANOMALY).json()
    assert body["baseline"]["years_used"] == 9
    assert body["warnings"] == ["History for 2020 could not be loaded and was left out."]


def test_too_many_missing_years_is_insufficient_history(client, upstream):
    def flaky(request):
        if request.url.params["start_date"][:4] in {"2016", "2017", "2018", "2019"}:
            return httpx.Response(500)
        return archive_response(request)
    upstream.archive.mock(side_effect=flaky)
    r = client.get(ANOMALY)
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "insufficient_history"


def test_archive_rate_limit_fails_the_whole_request(client, upstream):
    upstream.archive.respond(429)
    r = client.get(ANOMALY)
    assert r.status_code == 503
    assert r.headers["Retry-After"] == str(config.DEFAULT_RETRY_AFTER_S)


def test_unknown_route_uses_our_error_shape(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_five_years_with_one_failing_is_not_enough_history(client, upstream):
    """Review bug 1: 4 of 5 years pass the history check, but 4 x 7 = 28 samples per day is
    under the 30 minimum, so every day is unknown. That must not be reported as "normal"."""
    def flaky(request):
        if request.url.params["start_date"].startswith("2021"):
            return httpx.Response(500)
        return archive_response(request)
    upstream.archive.mock(side_effect=flaky)
    body = client.get(ANOMALY + "&years=5").json()
    assert body["baseline"]["years_used"] == 4
    assert body["days"][0]["high"]["n"] == 28
    assert body["days"][0]["high"]["level"] == "unknown"
    for part in ("highs", "lows"):
        assert body["week"][part]["verdict"] == "not_enough_history"
        assert body["week"][part]["days_judged"] == 0


# --- odd upstream shapes (review bug 3): 502, never a 500 ---------------------

def test_empty_forecast_is_502_not_500(client, upstream):
    upstream.forecast.respond(json={"timezone": "UTC", **daily([], [], [], [])})
    r = client.get(ANOMALY)
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "upstream_error"


def test_null_forecast_column_degrades_to_not_enough_history(client, upstream):
    payload = forecast_json()
    payload["daily"]["temperature_2m_max"] = None
    upstream.forecast.respond(json=payload)
    r = client.get(ANOMALY)
    assert r.status_code == 200
    assert r.json()["week"]["highs"]["verdict"] == "not_enough_history"
    assert r.json()["week"]["highs"]["days_without_forecast"] == 7
    assert r.json()["week"]["lows"]["verdict"] != "not_enough_history"


def test_list_shaped_geocoding_reply_is_502(client, upstream):
    upstream.geocode.respond(json=[{"name": "Denver"}])
    r = client.get("/api/cities?q=Denver")
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "upstream_error"


def test_odd_geocoding_fields_are_cleaned_not_500(client, upstream):
    odd = {**GEOCODE_DENVER["results"][0], "population": 729019.0, "id": "5419384"}
    upstream.geocode.respond(json={"results": [odd, "not a place", {"name": "No coords"}]})
    r = client.get("/api/cities?q=Denver")
    assert r.status_code == 200
    [place] = r.json()["results"]
    assert place["population"] == 729019
    assert place["id"] == 5419384


# --- more odd upstream shapes (second review, findings 1 and 8) ---------------

def test_text_temperature_in_forecast_is_502(client, upstream):
    payload = forecast_json()
    payload["daily"]["temperature_2m_max"][0] = "hot"
    upstream.forecast.respond(json=payload)
    r = client.get(ANOMALY)
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "upstream_error"


def test_text_temperature_in_one_archive_year_is_a_warning(client, upstream):
    def odd(request):
        resp = archive_response(request)
        if request.url.params["start_date"].startswith("2019"):
            body = resp.json()
            body["daily"]["temperature_2m_min"][0] = "cold"
            return httpx.Response(200, json=body)
        return resp
    upstream.archive.mock(side_effect=odd)
    body = client.get(ANOMALY).json()
    assert body["baseline"]["years_used"] == 9
    assert body["warnings"] == ["History for 2019 could not be loaded and was left out."]


def test_non_text_timezone_is_dropped_not_500(client, upstream):
    upstream.forecast.respond(json={**forecast_json(), "timezone": 7})
    r = client.get(ANOMALY)
    assert r.status_code == 200
    assert r.json()["location"]["timezone"] is None


@pytest.mark.parametrize("lat, lon", [
    (float("nan"), 0.0), (200.0, 0.0), (0.0, -181.0), (True, 0.0), ("40", "nope"),
])
def test_places_with_bad_coordinates_are_dropped(client, upstream, lat, lon):
    bad = {**GEOCODE_DENVER["results"][0], "name": "Bad", "latitude": lat, "longitude": lon}
    # sent as raw text: NaN isn't valid JSON, but Python's reader (and so ours) accepts it
    body = json.dumps({"results": [bad, GEOCODE_DENVER["results"][0]]})
    upstream.geocode.respond(content=body.encode(), headers={"Content-Type": "application/json"})
    r = client.get("/api/cities?q=Denver")
    assert r.status_code == 200
    assert [p["name"] for p in r.json()["results"]] == ["Denver"]
