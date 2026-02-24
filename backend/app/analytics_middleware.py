"""
Usage analytics middleware for FastAPI.
Logs API requests to shared_platform.api_request_log (fire-and-forget).
"""
import os
import time
import asyncio
import asyncpg
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

EXCLUDED_PATHS = {"/health", "/api/health", "/favicon.ico"}
EXCLUDED_PREFIXES = ("/assets/", "/static/")
EXCLUDED_EXTENSIONS = frozenset({
    ".js", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif",
    ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot",
})

_pool = None


async def _get_pool():
    global _pool
    if _pool is None:
        dsn = os.environ.get("PLATFORM_DATABASE_URL")
        if not dsn:
            return None
        try:
            _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2)
        except Exception as e:
            print(f"[analytics] Failed to create pool: {e}")
            return None
    return _pool


def _should_exclude(path: str) -> bool:
    if path in EXCLUDED_PATHS:
        return True
    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return True
    dot_idx = path.rfind(".")
    if dot_idx > 0:
        ext = path[dot_idx:].lower()
        if ext in EXCLUDED_EXTENSIONS:
            return True
    return False


async def _log_request(app_name, method, path, status_code, response_time_ms, user_id, ip_address):
    try:
        pool = await _get_pool()
        if pool is None:
            return
        await pool.execute(
            "INSERT INTO api_request_log (app_name, method, path, status_code, response_time_ms, user_id, ip_address) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7)",
            app_name, method, path, status_code, response_time_ms, user_id, ip_address,
        )
    except Exception as e:
        print(f"[analytics] Failed to log request: {e}")


class AnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, app_name: str = "advisor"):
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if _should_exclude(path):
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        response_time_ms = int((time.time() - start) * 1000)

        # Extract user from session (fire-and-forget)
        user_id = None
        session = getattr(request, "session", None) or {}
        if session.get("user"):
            user_id = session["user"].get("email") or session["user"].get("id")

        ip_address = request.client.host if request.client else None

        # Fire-and-forget: schedule the INSERT without awaiting in the response path
        asyncio.ensure_future(
            _log_request(
                self.app_name,
                request.method,
                path,
                response.status_code,
                response_time_ms,
                user_id,
                ip_address,
            )
        )

        return response
