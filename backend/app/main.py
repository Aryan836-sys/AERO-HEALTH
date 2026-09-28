"""
Aero Health backend entrypoint.
Run with: uvicorn app.main:app --reload
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.routers import admin, advisory, alerts, auth, favorites, locations, profile, readings, reports

load_dotenv()

app = FastAPI(
    title="Aero Health API",
    version="0.1.0",
    description="Backend API for Aero Health — real-time AQI, health advisories, "
    "favorites, alerts and community pollution reports.",
)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locations.router)
app.include_router(readings.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(advisory.router)
app.include_router(favorites.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/", tags=["health"])
def root():
    return {"service": "Aero Health API", "status": "ok"}


@app.get("/health", tags=["health"])
def health_check():
    """Verifies the API is up AND can reach PostgreSQL."""
    db_ok = True
    error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_ok = False
        error = str(exc)

    return {"api": "ok", "database": "ok" if db_ok else "unreachable", "error": error}