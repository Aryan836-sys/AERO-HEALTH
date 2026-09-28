"""Aero Health API entry point: app, middleware, router registration.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.limiter import limiter
from app.routers import (
    account,
    admin,
    advisory,
    alerts,
    auth,
    favorites,
    locations,
    readings,
    profile,
    reports,
)
from app.services.uploads import URL_PREFIX, upload_root

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if settings.cache_readings_enabled:
        # Show the job's per-run INFO summaries in the uvicorn console.
        logging.basicConfig(level=logging.INFO)
        # httpx logs full request URLs at INFO, including WAQI_TOKEN as a
        # query param -- keep it at WARNING so the token never hits the logs.
        logging.getLogger("httpx").setLevel(logging.WARNING)
        # Imported here: the job module reads WAQI_TOKEN at import time.
        from app.jobs.cache_readings import CACHE_INTERVAL_MINUTES, start_scheduler

        scheduler = start_scheduler()
        logger.info("Readings cache job started (every %d min).", CACHE_INTERVAL_MINUTES)
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(
    lifespan=lifespan,
    title="Aero Health API",
    version="0.1.0",
    description="Air quality for the Kathmandu Valley, with explainable health advisories.",
)

app.state.limiter = limiter
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # never "*" -- credentials are allowed
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


@app.middleware("http")
async def secure_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    # The Swagger UI loads scripts from a CDN, so the strict CSP skips it.
    if not request.url.path.startswith(_DOCS_PATHS):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


for module in (
    auth,
    account,
    locations,
    readings,
    profile,
    advisory,
    favorites,
    alerts,
    reports,
    admin,
):
    app.include_router(module.router)

# Report photos. Filenames are server-generated random names (see
# services/uploads.py), so nothing user-controlled is ever a path.
app.mount(URL_PREFIX, StaticFiles(directory=upload_root()), name="uploads")
