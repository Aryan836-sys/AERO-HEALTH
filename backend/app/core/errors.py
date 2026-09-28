"""One JSON error shape for every failure:

    {"detail": "<human message>", "status": 404, "code": "not_found"}

`detail` stays a plain string (the same key FastAPI uses) so clients that
already read `response.data.detail` keep working. Validation failures add an
`errors` list of {field, message}.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
}


def _body(status: int, detail: str, **extra) -> dict:
    return {"detail": detail, "status": status, "code": _CODES.get(status, "error"), **extra}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            _body(exc.status_code, detail),
            status_code=exc.status_code,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {
                "field": ".".join(
                    str(p) for p in e["loc"] if p not in ("body", "query", "path", "form")
                ),
                "message": e["msg"],
            }
            for e in exc.errors()
        ]
        return JSONResponse(
            _body(422, "Validation failed", errors=errors), status_code=422
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limited(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            _body(429, "Too many requests. Please slow down and try again."),
            status_code=429,
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        # Never leak internals to the client; the traceback goes to the log.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(_body(500, "Internal server error"), status_code=500)
