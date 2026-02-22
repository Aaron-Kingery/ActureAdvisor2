import os
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.api_v1.endpoints import health, chat, sync, admin
from app.auth.routes import router as auth_router
from app.auth.dependencies import require_auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

# --- Middleware ---

# Session middleware (signed cookie — must be added before routes)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie="advisor_session",
    max_age=8 * 60 * 60,  # 8 hours
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production",
)

# CORS — restricted to acture.ai subdomains (T2.4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://advisor.acture.ai",
        "https://expensification.acture.ai",
        "https://linecard.acture.ai",
        "https://onboarding.acture.ai",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# --- Scheduled sync ---

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.db import AsyncSessionLocal
from app.services.sync_service import SyncService
from app.services.rag_service import rag_service


async def run_sync_job():
    """Scheduled job to sync documents from SharePoint."""
    async with AsyncSessionLocal() as session:
        sync_svc = SyncService(session, rag_service)
        from app.services.connectors.sharepoint_connector import SharePointConnector

        connector = SharePointConnector(
            site_url=settings.SHAREPOINT_SITE_URL or "",
            client_id=settings.AZURE_AD_CLIENT_ID or "",
            client_secret=settings.AZURE_AD_CLIENT_SECRET or "",
            tenant_id=settings.AZURE_AD_TENANT_ID or "",
        )
        try:
            await sync_svc.sync_connector(connector)
        except Exception as e:
            print(f"Scheduled sync failed: {e}")


scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        run_sync_job, "interval", hours=4, id="doc_sync", replace_existing=True
    )
    scheduler.start()


# --- Routes ---

# Auth routes (public — no auth required)
app.include_router(auth_router)

# Health check (public)
app.include_router(health.router, prefix="/api", tags=["health"])

# Protected API routes — require authentication
app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["chat"],
    dependencies=[Depends(require_auth)],
)
app.include_router(
    sync.router,
    prefix="/api/sync",
    tags=["sync"],
    dependencies=[Depends(require_auth)],
)
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_auth)],
)

# --- Serve Frontend ---

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="static")

    # SPA catch-all: serve index.html for any non-API route
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # Don't serve frontend for API/auth routes (handled above)
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
