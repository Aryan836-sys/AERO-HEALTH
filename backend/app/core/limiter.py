"""Shared slowapi limiter, keyed by client IP.

Behind a reverse proxy, run uvicorn with --proxy-headers (and a trusted
--forwarded-allow-ips) so the key is the real client, not the proxy.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

limiter = Limiter(key_func=get_remote_address, enabled=get_settings().rate_limit_enabled)

AUTH_LIMIT = "10/minute"
PUBLIC_LIMIT = "120/minute"
WRITE_LIMIT = "30/minute"
# Reports accept guests and file uploads, so keep this one tighter.
REPORT_LIMIT = "10/minute"
