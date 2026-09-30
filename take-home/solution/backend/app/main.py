import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import config
from .errors import ApiError
from .openmeteo import OpenMeteo
from .routes import router

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    timeout = httpx.Timeout(config.READ_TIMEOUT_S, connect=config.CONNECT_TIMEOUT_S)
    async with httpx.AsyncClient(timeout=timeout) as http:
        app.state.openmeteo = OpenMeteo(http)
        yield


app = FastAPI(title="Is this week unusual?", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- one error shape for every response --------------------------------------

def error_response(status: int, code: str, message: str, retry_after_s: int | None = None):
    headers = {"Retry-After": str(retry_after_s)} if retry_after_s else None
    body = {"error": {"code": code, "message": message, "retry_after_s": retry_after_s}}
    return JSONResponse(status_code=status, content=body, headers=headers)


@app.exception_handler(ApiError)
async def handle_api_error(request, exc: ApiError):
    return error_response(exc.status, exc.code, exc.message, exc.retry_after_s)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"] if p not in ("query", "path", "body"))
        parts.append(f"{field}: {err['msg']}" if field else err["msg"])
    return error_response(422, "invalid_input", "; ".join(parts))


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request, exc: StarletteHTTPException):
    code = "not_found" if exc.status_code == 404 else "http_error"
    return error_response(exc.status_code, code, str(exc.detail))


@app.exception_handler(Exception)
async def handle_unexpected(request, exc: Exception):
    log.exception("Unhandled error")
    return error_response(500, "internal_error", "Something went wrong on our side.")
