from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.db import get_db
from app.services.rag_service import rag_service
from app.models import Query, Feedback, FeedbackType, FeedbackStatus

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class Source(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    response: str
    sources: List[Source]
    query_id: uuid.UUID
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(
    request_body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Chat endpoint -- requires auth (enforced at router level)."""
    user = request.session.get("user", {})
    user_email = user.get("email", "unknown")

    # Generate or use provided session ID for conversation continuity
    session_id = request_body.session_id or str(uuid.uuid4())

    # 1. Search (limit=5 to keep context focused and reduce noise)
    chunks = await rag_service.search(request_body.message, db, limit=5)

    # 2. Generate
    if not chunks:
        response_text = "I don't have information about that in our documentation."
        sources = []
        source_ids = []
    else:
        response_text = await rag_service.generate_response(
            request_body.message, chunks, session_id=session_id
        )
        sources = []
        seen_urls = set()
        source_ids = []
        for chunk in chunks:
            if chunk.document.source_url not in seen_urls:
                sources.append(
                    Source(title=chunk.document.title, url=chunk.document.source_url)
                )
                seen_urls.add(chunk.document.source_url)
            if chunk.document.id not in source_ids:
                source_ids.append(chunk.document.id)

    is_negative = "I don't have information about that" in response_text
    answered_status = False if is_negative else bool(chunks)

    # Store exchange in conversation memory even for no-result queries
    if not chunks and session_id:
        rag_service.conversation_store.add_exchange(
            session_id, request_body.message, response_text
        )

    # 3. Store Query
    new_query = Query(
        user_id=None,
        user_email=user_email,
        question=request_body.message,
        response=response_text,
        answered=answered_status,
        source_doc_ids=source_ids,
    )
    db.add(new_query)
    await db.commit()
    await db.refresh(new_query)

    # 4. Auto-flag unanswered
    if not new_query.answered:
        system_feedback = Feedback(
            query_id=new_query.id,
            feedback_type=FeedbackType.NEGATIVE,
            status=FeedbackStatus.NEW,
            admin_notes="System: Unable to answer from internal documents.",
        )
        db.add(system_feedback)
        await db.commit()

    return ChatResponse(
        response=response_text,
        sources=sources,
        query_id=new_query.id,
        session_id=session_id,
    )


class FeedbackCreate(BaseModel):
    feedback_type: str


@router.post("/{query_id}/feedback")
async def submit_feedback(
    query_id: uuid.UUID,
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for a query."""
    query = await db.get(Query, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    try:
        f_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid feedback type")

    new_feedback = Feedback(
        query_id=query_id,
        feedback_type=f_type,
        status=FeedbackStatus.NEW,
    )
    db.add(new_feedback)
    await db.commit()
    return {"status": "success"}
