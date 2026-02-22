from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db, AsyncSessionLocal
from app.services.rag_service import rag_service
from app.services.sync_service import SyncService
from app.services.connectors.sharepoint import SharePointConnector
from app.services.connectors.google_drive import GoogleDriveConnector

router = APIRouter()

async def execute_sync_background(connector_type: str):
    async with AsyncSessionLocal() as session:
        try:
            print(f"Starting background sync for {connector_type}...")
            service = SyncService(session, rag_service)
            if connector_type == "sharepoint":
                await service.sync_connector(SharePointConnector())
            elif connector_type == "google":
                await service.sync_connector(GoogleDriveConnector())
            print(f"Completed background sync for {connector_type}.")
        except Exception as e:
            print(f"Background Sync error ({connector_type}): {e}")

@router.post("/trigger")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    connector: str = "sharepoint"
):
    """
    Manually trigger synchronization for a specific connector (Background Task).
    """
    if connector not in ["sharepoint", "google"]:
        raise HTTPException(status_code=400, detail="Invalid connector type")
    
    background_tasks.add_task(execute_sync_background, connector)
    
    return {"status": "success", "message": f"Sync started for {connector}. Check dashboard for progress."}
