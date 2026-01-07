from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.db import get_db
from app.services.rag_service import rag_service
from app.models import Query, Feedback, User, FeedbackType, FeedbackStatus

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_email: Optional[str] = None

class Source(BaseModel):
    title: str
    url: str

class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    query_id: uuid.UUID

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Chat endpoint. Saves query and feedback placeholder.
    """
    # 0. Get User Context
    # Optimization: Store email directly to avoid lookup blocking. 
    # Fallback to simple "limit 1" to satisfy FK constraint without precise lookup if needed.
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    user_id = user.id if user else None

    # 1. Search
    chunks = await rag_service.search(request.message, db, limit=5)
    
    # 2. Generate
    if not chunks:
        response_text = "I don't have information about that in our documentation."
        sources = []
        source_ids = []
    else:
        response_text = await rag_service.generate_response(request.message, chunks)
        sources = []
        seen_urls = set()
        source_ids = []
        for chunk in chunks:
            if chunk.document.source_url not in seen_urls:
                sources.append(Source(title=chunk.document.title, url=chunk.document.source_url))
                seen_urls.add(chunk.document.source_url)
            if chunk.document.id not in source_ids:
                source_ids.append(chunk.document.id)

    # Refine answered status based on content
    is_negative_response = "I don't have information about that in our documentation" in response_text
    answered_status = False if is_negative_response else bool(chunks)

    # 3. Store Query
    new_query = Query(
        user_id=user_id, # Fallback or error if no user seeded? We seeded users.
        user_email=request.user_email, # Direct storage
        question=request.message,
        response=response_text,
        answered=answered_status,
        source_doc_ids=source_ids
    )
    db.add(new_query)
    await db.commit()
    await db.refresh(new_query)

    # 4. Auto-flag if unanswered (FR-4.3, FR-5.2)
    if not new_query.answered:
        system_feedback = Feedback(
            query_id=new_query.id,
            feedback_type=FeedbackType.NEGATIVE,
            status=FeedbackStatus.NEW,
            admin_notes="System: Unable to answer from internal documents."
        )
        db.add(system_feedback)
        await db.commit()

    return ChatResponse(
        response=response_text,
        sources=sources,
        query_id=new_query.id
    )

class FeedbackCreate(BaseModel):
    feedback_type: str # "positive" or "negative"

@router.post("/{query_id}/feedback")
async def submit_feedback(
    query_id: uuid.UUID, 
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a query.
    """
    # Check query exists
    query = await db.get(Query, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    # Map string to enum
    try:
        f_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid feedback type")

    # Create Feedback
    new_feedback = Feedback(
        query_id=query_id,
        feedback_type=f_type,
        status=FeedbackStatus.NEW
    )
    db.add(new_feedback)
    await db.commit()
    return {"status": "success"}
