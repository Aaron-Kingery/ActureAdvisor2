from typing import List, Tuple, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk
from app.core.config import settings
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.messages import SystemMessage, HumanMessage
import uuid
import hashlib

# Import OpenAI optionally
try:
    from langchain_openai import ChatOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class RAGService:
    def __init__(self):
        # Embeddings
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            from langchain_openai import OpenAIEmbeddings
            self.embeddings = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model="text-embedding-3-small"
            )
            # OpenAI LLM
            self.openai_llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o",
                temperature=0.7
            )
            # Initialize Ollama as fallback
            self.ollama_llm = OllamaLLM(
                base_url=settings.OLLAMA_BASE_URL,
                model="mistral" 
            )
        else:
            # Fallback to Ollama
            self.embeddings = OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model="nomic-embed-text"
            )
            self.ollama_llm = OllamaLLM(
                base_url=settings.OLLAMA_BASE_URL,
                model="mistral" 
            )
            self.openai_llm = None

        # Accuracy > Speed configuration
        # Larger chunks (approx 1-2 pages) ensure lists and tables aren't split.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=1000
        )

    async def _get_embedding(self, text: str) -> List[float]:
        return await self.embeddings.aembed_query(text)

    async def process_document(self, document: Document, content: str, session: AsyncSession):
        """
        Chunks document content, generates embeddings, and saves to DB.
        """
        chunks = self.text_splitter.create_documents([content])
        
        # Prepare texts
        texts = [chunk.page_content for chunk in chunks]
        
        # Batch Async Embeddings (Prevents blocking Event Loop)
        if HAS_OPENAI and settings.OPENAI_API_KEY:
            embeddings = await self.embeddings.aembed_documents(texts)
        else:
             # OllamaFallback might not support batch async well, but we try standard embed_documents or query loop
             # For Nomic (Ollama), we can iterate or use embed_documents if supported
             # But using aembed_query in loop is safer for concurrency yield
             embeddings = []
             for text in texts:
                 embeddings.append(await self._get_embedding(text))

        for i, chunk in enumerate(chunks):
            embedding = embeddings[i]
            
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk.page_content,
                embedding=embedding,
                metadata={"source": document.source_url}
            )
            session.add(db_chunk)
    
    async def search(self, query: str, session: AsyncSession, limit: int = 3) -> List[DocumentChunk]:
        """
        Performs vector search for relevant chunks.
        """
        query_embedding = await self._get_embedding(query)
        
        stmt = select(DocumentChunk).options(selectinload(DocumentChunk.document)).order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await session.execute(stmt)
        chunks = result.scalars().all()
        return chunks

    async def generate_response(self, query: str, context_chunks: List[DocumentChunk]) -> str:
        """
        Generates a response using the LLM with fallback logic.
        """
        context_text = "\n\n".join([
            f"Source: {chunk.document.title}\nContent:\n{chunk.content}" 
            for chunk in context_chunks
        ])
        
        system_prompt = f"""You are Acture Advisor, an AI assistant for Acture Solutions.
Use the following pieces of context to answer the user's question.
If the answer is not in the context, say "I don't have information about that in our documentation."
Do not try to make up an answer.

Context:
{context_text}
"""
        user_prompt = f"Question: {query}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        # Try OpenAI First
        if self.openai_llm:
            try:
                response = await self.openai_llm.ainvoke(messages)
                return response.content
            except Exception as e:
                print(f"OpenAI failed ({e}), falling back to Ollama...")
        
        # Fallback to Ollama
        response = await self.ollama_llm.ainvoke(messages)
        if hasattr(response, 'content'):
            return response.content
        return str(response)

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
                print(f"OpenAI failed ({e}), falling back to Ollama...")
        
        # Fallback
        response = await self.ollama_llm.ainvoke(messages)
        if hasattr(response, 'content'):
            return response.content
        return str(response)

rag_service = RAGService()
