"""Errors the API returns. Each has one HTTP status and one `code`."""


class ApiError(Exception):
    status = 500
    code = "internal_error"

    def __init__(self, message: str, retry_after_s: int | None = None):
        super().__init__(message)
        self.message = message
        self.retry_after_s = retry_after_s


class InvalidInput(ApiError):
    status = 422
    code = "invalid_input"


class CityNotFound(ApiError):
    status = 404
    code = "city_not_found"


class UpstreamRateLimited(ApiError):
    status = 503
    code = "upstream_rate_limited"


class UpstreamTimeout(ApiError):
    status = 504
    code = "upstream_timeout"


class UpstreamError(ApiError):
    status = 502
    code = "upstream_error"


class InsufficientHistory(ApiError):
    status = 502
    code = "insufficient_history"
