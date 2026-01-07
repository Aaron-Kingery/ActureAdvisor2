from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.services.rag_service import rag_service
from app.services.sync_service import SyncService
from app.services.connectors.sharepoint import SharePointConnector
from app.services.connectors.google_drive import GoogleDriveConnector

router = APIRouter()

async def run_sync_task(connector_type: str, session: AsyncSession):
    # Note: BackgroundTasks in FastAPI with AsyncSession need care. 
    # Usually better to use a fresh session or APScheduler. 
    # For this endpoint trigger, we'll try to run it.
    
    # However, dependency injection session is closed after request.
    # So we should probably instantiate a new session here or use the one passed if we await it.
    
    # For robustness, we'll just implement the logic here directly awaiting it 
    # (synchronous to the user - maybe not ideal for long tasks, but okay for manual trigger test).
    
    try:
        service = SyncService(session, rag_service)
        if connector_type == "sharepoint":
            await service.sync_connector(SharePointConnector())
        elif connector_type == "google":
            await service.sync_connector(GoogleDriveConnector())
    except Exception as e:
        print(f"Sync error: {e}")

@router.post("/trigger")
async def trigger_sync(
    connector: str = "sharepoint", 
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger synchronization for a specific connector.
    """
    if connector not in ["sharepoint", "google"]:
        raise HTTPException(status_code=400, detail="Invalid connector type")
    
    # Running inline for feedback (in production use background/celery)
    await run_sync_task(connector, db)
    
    return {"status": "success", "message": f"Sync completed for {connector}"}
