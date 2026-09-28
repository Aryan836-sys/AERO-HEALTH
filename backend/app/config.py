"""All runtime configuration, loaded from the environment / backend/.env.

Nothing secret is hardcoded: JWT_SECRET has no default on purpose, so a
missing secret stops the app at startup instead of silently signing tokens
with a well-known value.
"""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # Comma-separated. Lock this to the real frontend origin in production.
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # "development" | "production" | "test" -- production turns on HSTS.
    environment: str = "development"

    # Optional: enables the modelled fallback in services/resolver.py.
    owm_api_key: str | None = None

    upload_dir: str = "uploads"
    max_upload_mb: int = 5

    rate_limit_enabled: bool = True

    # Fetch fresh WAQI/OpenAQ readings in the background while the API runs
    # (jobs/cache_readings.py). Turn off if the job runs as its own process.
    cache_readings_enabled: bool = True

    # The refresh token also travels in an HttpOnly cookie so browser JS
    # never has to store it. Use "none" only when the frontend is on a
    # different site than the API (requires HTTPS).
    cookie_samesite: str = "lax"
    refresh_cookie_name: str = "aero_refresh"

    @field_validator("environment")
    @classmethod
    def _known_environment(cls, value: str) -> str:
        if value not in {"development", "production", "test"}:
            raise ValueError("environment must be development, production or test")
        return value

    @field_validator("cookie_samesite")
    @classmethod
    def _known_samesite(cls, value: str) -> str:
        if value not in {"lax", "strict", "none"}:
            raise ValueError("cookie_samesite must be lax, strict or none")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
