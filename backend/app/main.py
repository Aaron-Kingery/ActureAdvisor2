from fastapi import FastAPI
from app.core.config import settings
from app.api.api_v1.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.db import AsyncSessionLocal
from app.services.sync_service import SyncService
from app.services.rag_service import rag_service

# Assuming we have a way to init connector, or we do it inline

async def run_sync_job():
    """
    Scheduled job to sync documents.
    """
    # Create a fresh session for the background job
    async with AsyncSessionLocal() as session:
        sync_svc = SyncService(session, rag_service)
        # We need to know WHICH connector to sync. 
        # Spec says "Configured source". 
        # For Phase 1, we likely default to what's in env or just SharePoint.
        # We'll try to instantiate the SharePoint connector.
        # Ideally this is cleaner but effectively:
        from app.services.connectors.sharepoint_connector import SharePointConnector
        from app.core.config import settings
        
        # Simple loginless sync if credentials env vars are set
        connector = SharePointConnector(
            site_url=settings.SHAREPOINT_SITE_URL or "",
            client_id=settings.AZURE_AD_CLIENT_ID or "",
            client_secret=settings.AZURE_AD_CLIENT_SECRET or "",
            tenant_id=settings.AZURE_AD_TENANT_ID or ""
        )
        
        print("Starting scheduled sync...")
        try:
            await sync_svc.sync_connector(connector)
            print("Scheduled sync completed successfully.")
        except Exception as e:
            print(f"Scheduled sync failed: {e}")

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    # FR-2.3: Sync every 4 hours
    scheduler.add_job(run_sync_job, 'interval', hours=4, id="doc_sync", replace_existing=True)
    scheduler.start()

from fastapi.middleware.cors import CORSMiddleware

# Explicitly define origins for dev troubleshooting
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]

# Merge with settings if available (and parse string if needed)
if settings.BACKEND_CORS_ORIGINS:
    for origin in settings.BACKEND_CORS_ORIGINS:
        origins.append(str(origin))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
from app.api.api_v1.endpoints import chat, sync, admin
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

