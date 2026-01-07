from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models import User, Feedback, Query, Document, KBTemplate, Role, FeedbackStatus
from app.services.rag_service import rag_service
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

# --- Schemas ---
class StatsResponse(BaseModel):
    total_queries: int
    total_documents: int
    pending_feedback: int
    total_users: int
    success_rate: float

class FeedbackRead(BaseModel):
    id: uuid.UUID
    query_id: uuid.UUID
    feedback_type: str
    status: str
    admin_notes: str | None
    created_at: datetime
    query_text: str | None # Enriched
    response_text: str | None

    class Config:
        from_attributes = True

class FeedbackUpdate(BaseModel):
    status: FeedbackStatus
    admin_notes: str | None

class TemplateCreate(BaseModel):
    name: str
    template_content: str

class TemplateRead(TemplateCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    source_url: str
    file_type: str
    last_synced: datetime
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/documents", response_model=List[DocumentRead])
async def list_documents(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    List indexed documents.
    """
    result = await db.execute(select(Document).order_by(desc(Document.last_synced)).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Get system-wide statistics.
    """
    # Total Queries
    q_result = await db.execute(select(func.count(Query.id)))
    total_queries = q_result.scalar() or 0
    
    # Total Documents
    d_result = await db.execute(select(func.count(Document.id)))
    total_documents = d_result.scalar() or 0
    
    # Pending Feedback
    f_result = await db.execute(select(func.count(Feedback.id)).where(Feedback.status == FeedbackStatus.NEW))
    pending_feedback = f_result.scalar() or 0
    
    # Total Users
    u_result = await db.execute(select(func.count(User.id)))
    total_users = u_result.scalar() or 0
    
    # Success Rate (FR-5.6)
    # Answered / Total Queries
    a_result = await db.execute(select(func.count(Query.id)).where(Query.answered == True))
    answered_queries = a_result.scalar() or 0
    
    success_rate = 0.0
    if total_queries > 0:
        success_rate = (answered_queries / total_queries) * 100.0
    
    return StatsResponse(
        total_queries=total_queries,
        total_documents=total_documents,
        pending_feedback=pending_feedback,
        total_users=total_users,
        success_rate=round(success_rate, 1)
    )

@router.get("/feedback", response_model=List[FeedbackRead])
async def list_feedback(
    status: FeedbackStatus | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List feedback items, optionally filtered by status.
    """
    stmt = select(Feedback).order_by(desc(Feedback.created_at)).limit(limit)
    if status:
        stmt = stmt.where(Feedback.status == status)
    
    result = await db.execute(stmt)
    feedbacks = result.scalars().all()
    
    # Enrich with query text (N+1 crude fix, acceptable for small admin backend)
    # Ideally use a join in the initial select
    response_list = []
    for fb in feedbacks:
        query = await db.get(Query, fb.query_id)
        response_list.append(FeedbackRead(
            id=fb.id,
            query_id=fb.query_id,
            feedback_type=fb.feedback_type.value,
            status=fb.status.value,
            admin_notes=fb.admin_notes,
            created_at=fb.created_at,
            query_text=query.question if query else None,
            response_text=query.response if query else None
        ))
        
    return response_list

@router.patch("/feedback/{feedback_id}", response_model=FeedbackRead)
async def update_feedback(
    feedback_id: uuid.UUID,
    update_data: FeedbackUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update feedback status and notes.
    """
    feedback = await db.get(Feedback, feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.status = update_data.status
    if update_data.admin_notes is not None:
        feedback.admin_notes = update_data.admin_notes
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    # Re-fetch for enrichment
    query = await db.get(Query, feedback.query_id)
    return FeedbackRead(
        id=feedback.id,
        query_id=feedback.query_id,
        feedback_type=feedback.feedback_type.value,
        status=feedback.status.value,
        admin_notes=feedback.admin_notes,
        created_at=feedback.created_at,
        query_text=query.question if query else None,
        response_text=query.response if query else None
    )

@router.get("/templates", response_model=List[TemplateRead])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KBTemplate).order_by(KBTemplate.name))
    return result.scalars().all()

@router.post("/templates", response_model=TemplateRead)
async def create_template(template: TemplateCreate, db: AsyncSession = Depends(get_db)):
    new_template = KBTemplate(
        name=template.name,
        template_content=template.template_content
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)
    return new_template

class KBFormatRequest(BaseModel):
    raw_text: str
    template_id: uuid.UUID

class KBFormatResponse(BaseModel):
    formatted_text: str

@router.post("/kb/format", response_model=KBFormatResponse)
async def format_kb_article(
    request: KBFormatRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Format raw text using AI and selected template.
    """
    template = await db.get(KBTemplate, request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    formatted_text = await rag_service.format_article(request.raw_text, template.template_content)
    return KBFormatResponse(formatted_text=formatted_text)

class KBPublishRequest(BaseModel):
    title: str
    content: str
    destination: str = "sharepoint" # placeholder

@router.post("/kb/publish")
async def publish_kb_article(request: KBPublishRequest):
    """
    Publish article to SharePoint.
    """
    try:
        # Instantiate Connector (Phase 1: Assume SharePoint)
        # Using local import to avoid circular dep if any, though unlikely here
        from app.services.connectors.sharepoint import SharePointConnector
        
        connector = SharePointConnector()
        
        # Determine filename (slugify title)
        safe_title = "".join(c for c in request.title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}.md"
        
        web_url = await connector.upload_file(filename, request.content)
        
        return {"status": "success", "message": f"Published: {web_url}", "url": web_url}
        
    except Exception as e:
        print(f"Publish failed: {e}")
        # Return 500 but with detail
        raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")
