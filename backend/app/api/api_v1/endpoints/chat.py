from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
import uuid

from app.core.db import get_db
from app.services.rag_service import rag_service
from app.models import Query, Feedback

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

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
    Chat endpoint. For Phase 1, assumes anonymous or single test user.
    """
    # 1. Search
    chunks = await rag_service.search(db, request.message)
    
    # 2. Generate
    if not chunks:
        return ChatResponse(
            response="I don't have information about that in our documentation.",
            sources=[],
            query_id=uuid.uuid4() # dummy
        )
        
    response_text = await rag_service.generate_response(request.message, chunks)
    
    # 3. Store Query (Optional for Phase 1 deliverable)
    # Skipped for now.
    
    sources = []
    seen_urls = set()
    
    for chunk in chunks:
        # Assuming eager load worked, otherwise this might fail if attributes missing
        # We need to ensure search does eager loading.
        if chunk.document.source_url not in seen_urls:
            sources.append(Source(title=chunk.document.title, url=chunk.document.source_url))
            seen_urls.add(chunk.document.source_url)
    
    return ChatResponse(
        response=response_text,
        sources=sources,
        query_id=uuid.uuid4()
    )
