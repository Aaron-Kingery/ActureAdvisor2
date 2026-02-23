import re
import time
import threading
from typing import List, Dict, Tuple, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from sqlalchemy import select, text, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk
from app.core.config import settings
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.messages import SystemMessage, HumanMessage
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)

# Import OpenAI optionally
try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Import cross-encoder optionally
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    logger.warning("sentence-transformers not installed; cross-encoder re-ranking disabled")

# Minimum chunk length (characters) -- chunks below this are too short
# to produce meaningful embeddings and pollute search results
MIN_CHUNK_LENGTH = 100

# Maximum cosine distance for search results -- chunks further than this
# are considered irrelevant (0.0 = identical, 2.0 = opposite)
MAX_COSINE_DISTANCE = 0.4

# RRF constant -- standard value from the original RRF paper
RRF_K = 60

# Parent-child chunking: small children for retrieval, large parents for LLM context
PARENT_CHUNK_SIZE = 2000
PARENT_CHUNK_OVERLAP = 300
CHILD_CHUNK_SIZE = 500
CHILD_CHUNK_OVERLAP = 50

# Conversation history settings
CONVERSATION_MAX_EXCHANGES = 5
CONVERSATION_TTL_SECONDS = 3600  # 1 hour


def normalize_whitespace(content: str) -> str:
    """Collapse 3+ consecutive newlines to 2, strip trailing whitespace per line."""
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


class ConversationStore:
    """In-memory conversation history with TTL-based expiry."""

    def __init__(self, max_exchanges: int = CONVERSATION_MAX_EXCHANGES, ttl: int = CONVERSATION_TTL_SECONDS):
        self._store: Dict[str, Dict] = {}
        self._max_exchanges = max_exchanges
        self._ttl = ttl
        self._lock = threading.Lock()

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with self._lock:
            entry = self._store.get(session_id)
            if not entry:
                return []
            if time.time() - entry["last_access"] > self._ttl:
                del self._store[session_id]
                return []
            entry["last_access"] = time.time()
            return list(entry["exchanges"])

    def add_exchange(self, session_id: str, question: str, answer: str):
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = {"exchanges": [], "last_access": time.time()}
            entry = self._store[session_id]
            entry["last_access"] = time.time()
            entry["exchanges"].append({"question": question, "answer": answer})
            # Keep only the last N exchanges
            if len(entry["exchanges"]) > self._max_exchanges:
                entry["exchanges"] = entry["exchanges"][-self._max_exchanges:]

    def cleanup_expired(self):
        """Remove expired sessions. Called periodically."""
        now = time.time()
        with self._lock:
            expired = [sid for sid, e in self._store.items() if now - e["last_access"] > self._ttl]
            for sid in expired:
                del self._store[sid]


class RAGService:
    def __init__(self):
        # Embeddings -- text-embedding-3-large (3072 dims, higher quality)
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            from langchain_openai import OpenAIEmbeddings
            self.embeddings = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model="text-embedding-3-large", dimensions=2000
            )
            # OpenAI LLM -- gpt-4o-mini: better quality AND cheaper than gpt-3.5-turbo
            self.openai_llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o-mini",
                temperature=0.1
            )
        else:
            # Fallback to Ollama
            self.embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model="nomic-embed-text"
            )
            self.openai_llm = None

        # Parent chunker (2000 chars -- used for LLM context)
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=PARENT_CHUNK_SIZE,
            chunk_overlap=PARENT_CHUNK_OVERLAP
        )
        # Child chunker (500 chars -- used for retrieval/embedding)
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHILD_CHUNK_SIZE,
            chunk_overlap=CHILD_CHUNK_OVERLAP
        )

        # Cross-encoder for re-ranking
        self.cross_encoder = None
        if HAS_CROSS_ENCODER:
            try:
                self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                logger.info("Cross-encoder model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")

        # Conversation memory
        self.conversation_store = ConversationStore()

    async def _get_embedding(self, text: str) -> List[float]:
        return await self.embeddings.aembed_query(text)

    async def process_document(self, document: Document, content: str, session: AsyncSession):
        """
        Parent-child chunking: creates large parent chunks (2000 chars) for LLM context
        and smaller child chunks (500 chars) for embedding/retrieval.
        Child chunks reference their parent via parent_chunk_id.
        Uses pre-generated UUIDs to avoid flush() inside the loop.
        """
        # Normalize whitespace before chunking
        content = normalize_whitespace(content)

        # Create parent chunks
        parent_docs = self.parent_splitter.create_documents([content])
        parent_docs = [p for p in parent_docs if len(p.page_content.strip()) >= MIN_CHUNK_LENGTH]

        if not parent_docs:
            logger.warning(f"No valid chunks produced for {document.title}")
            return

        # Collect all texts that need embedding
        embed_tasks = []  # (parent_idx, child_idx_or_none, text)
        parent_child_map = []  # (parent_idx, child_docs)

        for parent_idx, parent_doc in enumerate(parent_docs):
            child_docs = self.child_splitter.create_documents([parent_doc.page_content])
            child_docs = [c for c in child_docs if len(c.page_content.strip()) >= MIN_CHUNK_LENGTH]

            if not child_docs:
                # Parent is too small to split -- embed it directly
                embed_tasks.append((parent_idx, None, parent_doc.page_content))
                parent_child_map.append((parent_idx, []))
            else:
                for child_idx, child_doc in enumerate(child_docs):
                    embed_tasks.append((parent_idx, child_idx, child_doc.page_content))
                parent_child_map.append((parent_idx, child_docs))

        # Batch embed all texts at once
        all_texts = [t[2] for t in embed_tasks]
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            all_embeddings = await self.embeddings.aembed_documents(all_texts)
        else:
            all_embeddings = [await self._get_embedding(t) for t in all_texts]

        # Build embedding lookup
        embed_lookup = {}
        for i, (parent_idx, child_idx, _text) in enumerate(embed_tasks):
            embed_lookup[(parent_idx, child_idx)] = all_embeddings[i]

        # Create DB records with pre-generated UUIDs
        total_children = 0
        for parent_idx, parent_doc in enumerate(parent_docs):
            parent_id = uuid.uuid4()
            _, child_docs = parent_child_map[parent_idx]

            parent_embedding = embed_lookup.get((parent_idx, None))

            parent_chunk = DocumentChunk(
                id=parent_id,
                document_id=document.id,
                chunk_index=parent_idx,
                content=parent_doc.page_content,
                embedding=parent_embedding,
                parent_chunk_id=None,
                metadata={"source": document.source_url, "chunk_type": "parent"}
            )
            session.add(parent_chunk)

            if not child_docs:
                total_children += 1
            else:
                for child_idx, child_doc in enumerate(child_docs):
                    child_chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_index=parent_idx * 100 + child_idx,
                        content=child_doc.page_content,
                        embedding=embed_lookup[(parent_idx, child_idx)],
                        parent_chunk_id=parent_id,
                        metadata={"source": document.source_url, "chunk_type": "child"}
                    )
                    session.add(child_chunk)
                    total_children += 1

        logger.info(f"Processed {document.title}: {len(parent_docs)} parents, {total_children} children")
        # search_vector (tsvector) is auto-generated by a PostgreSQL trigger on INSERT

    async def _vector_search(self, query_embedding: List[float], session: AsyncSession, limit: int = 15) -> List[Tuple[DocumentChunk, int]]:
        """Vector similarity search on child chunks. Returns (chunk, rank) pairs."""
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.embedding.isnot(None))
            .where(DocumentChunk.embedding.cosine_distance(query_embedding) < MAX_COSINE_DISTANCE)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await session.execute(stmt)
        chunks = result.scalars().all()
        return [(chunk, rank) for rank, chunk in enumerate(chunks)]

    async def _keyword_search(self, query: str, session: AsyncSession, limit: int = 15) -> List[Tuple[DocumentChunk, int]]:
        """BM25 keyword search using PostgreSQL full-text search. Returns (chunk, rank) pairs."""
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.search_vector.op('@@')(func.plainto_tsquery('english', query)))
            .order_by(func.ts_rank_cd(DocumentChunk.search_vector, func.plainto_tsquery('english', query)).desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        chunks = result.scalars().all()
        return [(chunk, rank) for rank, chunk in enumerate(chunks)]

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Tuple[DocumentChunk, int]],
        keyword_results: List[Tuple[DocumentChunk, int]],
        limit: int = 5
    ) -> List[DocumentChunk]:
        """
        Merge vector and keyword results using Reciprocal Rank Fusion.
        RRF score = sum(1 / (k + rank + 1)) across both result lists.
        """
        scores: Dict[uuid.UUID, float] = {}
        chunk_map: Dict[uuid.UUID, DocumentChunk] = {}

        for chunk, rank in vector_results:
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            chunk_map[chunk.id] = chunk

        for chunk, rank in keyword_results:
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            chunk_map[chunk.id] = chunk

        # Sort by RRF score descending, take top N
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        return [chunk_map[cid] for cid in sorted_ids[:limit]]

    def _rerank(self, query: str, chunks: List[DocumentChunk], top_n: int = 5) -> List[DocumentChunk]:
        """Re-rank chunks using cross-encoder. Falls back to returning chunks as-is if unavailable."""
        if not self.cross_encoder or len(chunks) <= top_n:
            return chunks[:top_n]

        try:
            pairs = [[query, chunk.content] for chunk in chunks]
            scores = self.cross_encoder.predict(pairs)
            scored = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
            return [chunk for chunk, score in scored[:top_n]]
        except Exception as e:
            logger.warning(f"Cross-encoder re-ranking failed: {e}")
            return chunks[:top_n]

    async def _resolve_parents(self, chunks: List[DocumentChunk], session: AsyncSession) -> List[DocumentChunk]:
        """For child chunks, fetch and return their parent chunks instead (richer context for LLM)."""
        parent_ids = set()
        standalone = []
        for chunk in chunks:
            if chunk.parent_chunk_id:
                parent_ids.add(chunk.parent_chunk_id)
            else:
                standalone.append(chunk)

        if not parent_ids:
            return chunks

        # Fetch parent chunks
        parent_stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.id.in_(parent_ids))
        )
        result = await session.execute(parent_stmt)
        parents = result.scalars().all()

        # Deduplicate: combine parents with standalone chunks
        seen_ids = set()
        resolved = []
        for p in parents:
            if p.id not in seen_ids:
                resolved.append(p)
                seen_ids.add(p.id)
        for c in standalone:
            if c.id not in seen_ids:
                resolved.append(c)
                seen_ids.add(c.id)

        return resolved

    async def search(self, query: str, session: AsyncSession, limit: int = 5) -> List[DocumentChunk]:
        """
        Hybrid search: runs vector similarity and BM25 keyword search in parallel,
        merges with Reciprocal Rank Fusion, re-ranks with cross-encoder,
        resolves child->parent for richer LLM context,
        then expands with neighbor chunks.
        """
        query_embedding = await self._get_embedding(query)

        # Run both searches (vector uses the embedding, keyword uses raw text)
        vector_results = await self._vector_search(query_embedding, session, limit=15)
        keyword_results = await self._keyword_search(query, session, limit=15)

        logger.info(f"Search for '{query[:50]}': {len(vector_results)} vector hits, {len(keyword_results)} keyword hits")

        # If both are empty, nothing to return
        if not vector_results and not keyword_results:
            return []

        # Merge with RRF -- get more candidates for re-ranking
        rrf_candidates = self._reciprocal_rank_fusion(vector_results, keyword_results, limit=15)

        if not rrf_candidates:
            return []

        # Re-rank with cross-encoder to pick the best chunks
        matched_chunks = self._rerank(query, rrf_candidates, top_n=limit)

        if not matched_chunks:
            return []

        # Resolve child chunks to their parents for richer LLM context
        matched_chunks = await self._resolve_parents(matched_chunks, session)

        # Neighbor expansion: for each matched chunk, also fetch chunk_index +/- 1
        # from the same document (only for parent/standalone chunks, not children)
        seen_ids = {c.id for c in matched_chunks}
        neighbor_conditions = []
        for chunk in matched_chunks:
            if chunk.parent_chunk_id is None:  # Only expand parent/standalone chunks
                for offset in (-1, 1):
                    neighbor_conditions.append(
                        (DocumentChunk.document_id == chunk.document_id) &
                        (DocumentChunk.chunk_index == chunk.chunk_index + offset) &
                        (DocumentChunk.parent_chunk_id.is_(None))
                    )

        if neighbor_conditions:
            neighbor_stmt = (
                select(DocumentChunk)
                .options(selectinload(DocumentChunk.document))
                .where(or_(*neighbor_conditions))
            )
            neighbor_result = await session.execute(neighbor_stmt)
            neighbors = neighbor_result.scalars().all()

            for n in neighbors:
                if n.id not in seen_ids:
                    matched_chunks.append(n)
                    seen_ids.add(n.id)

        # Sort all chunks by document then chunk_index for coherent context
        matched_chunks.sort(key=lambda c: (str(c.document_id), c.chunk_index))

        return matched_chunks

    async def generate_response(self, query: str, context_chunks: List[DocumentChunk], session_id: Optional[str] = None) -> str:
        """
        Generates a response using the LLM with fallback logic.
        Includes conversation history when session_id is provided.
        """
        context_text = "\n\n---\n\n".join([
            f"[Source: {chunk.document.title}]\n{chunk.content}"
            for chunk in context_chunks
        ])

        # Build conversation history context
        history_text = ""
        if session_id:
            history = self.conversation_store.get_history(session_id)
            if history:
                history_lines = []
                for exchange in history:
                    history_lines.append(f"User: {exchange['question']}")
                    # Truncate long answers in history to save tokens
                    answer = exchange['answer']
                    if len(answer) > 500:
                        answer = answer[:500] + "..."
                    history_lines.append(f"Assistant: {answer}")
                history_text = "\n".join(history_lines)

        system_prompt = f"""You are Acture Advisor, an AI assistant for Acture Solutions -- a Managed Service Provider specializing in K-12 educational technology and corporate IT.

Your job is to answer questions using ONLY the context provided below. Follow these rules strictly:

1. Base your answer exclusively on the provided context. Do not use outside knowledge.
2. If the context does not contain enough information to answer, say "I don't have information about that in our documentation."
3. When answering, mention which source document(s) the information comes from.
4. Use clear, professional language appropriate for IT administrators and school district staff.
5. Format your answers with bullet points or numbered steps when listing procedures or multiple items.
6. If the question is ambiguous, answer the most likely interpretation and note other possibilities.
7. Do not fabricate, speculate, or extrapolate beyond what the context states.

Context:
{context_text}
"""

        if history_text:
            system_prompt += f"""
Previous conversation (use this to understand follow-up questions):
{history_text}
"""

        user_prompt = query

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Try OpenAI First
        if self.openai_llm:
            try:
                response = await self.openai_llm.ainvoke(messages)
                response_text = response.content
            except Exception as e:
                logger.error(f"OpenAI failed ({e}), falling back to Ollama...")
                response = await self.ollama_llm.ainvoke(messages)
                response_text = response.content if hasattr(response, 'content') else str(response)
        else:
            # Fallback to Ollama
            response = await self.ollama_llm.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

        # Store exchange in conversation memory
        if session_id:
            self.conversation_store.add_exchange(session_id, query, response_text)

        return response_text

    async def format_article(self, raw_text: str, template_content: str) -> str:
        """
        Formats raw text into a KB article using the provided template.
        """
        system_prompt = f"""You are an expert technical writer for Acture Solutions.
Your goal is to rewrite the input text to match the structure and style of the provided Template.

Template Rules:
{template_content}

Instructions:
1. Reorganize the information to fit the template headers and sections.
2. Improve clarity, grammar, and professional tone.
3. Fix formatting (lists, code blocks, etc.).
4. Do NOT make up information that isn't in the source text.
5. Return ONLY the formatted Markdown content.
"""
        user_prompt = f"Raw Text:\n{raw_text}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        # Prefer OpenAI for formatting quality
        if self.openai_llm:
            try:
                response = await self.openai_llm.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"OpenAI failed ({e}), falling back to Ollama...")

        # Fallback
        response = await self.ollama_llm.ainvoke(messages)
        if hasattr(response, 'content'):
            return response.content
        return str(response)

rag_service = RAGService()
