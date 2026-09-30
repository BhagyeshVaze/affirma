"""Tunable settings in one place."""

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Upstream calls took about 0.4 s when planning, so these leave plenty of room.
CONNECT_TIMEOUT_S = 3.0
READ_TIMEOUT_S = 8.0
RETRY_DELAY_S = 0.5
DEFAULT_RETRY_AFTER_S = 60

# Open-Meteo allows 600 calls a minute per IP. Stay under it.
MAX_CONCURRENT_UPSTREAM = 5
UPSTREAM_BUDGET_PER_MIN = 500

GEOCODE_TTL_S = 24 * 3600
FORECAST_TTL_S = 30 * 60
ARCHIVE_TTL_S = 7 * 24 * 3600
CACHE_MAX_ENTRIES = 2000

CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
