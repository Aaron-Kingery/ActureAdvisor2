from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk
from app.services.ollama_service import ollama_service
import uuid

class RAGService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            length_function=len, # Optimally use tiktoken, but len is simple for now or use 'from_tiktoken_encoder' if needed
            is_separator_regex=False,
        )
        self.embeddings = ollama_service.get_embeddings()
        self.llm = ollama_service.get_llm()

    async def process_document(self, session: AsyncSession, doc_title: str, doc_url: str, doc_content: str, file_type: str) -> uuid.UUID:
        """
        Process a document: create Document record, chunk content, generate embeddings, save chunks.
        """
        # Create Document record
        import hashlib
        content_hash = hashlib.sha256(doc_content.encode('utf-8')).hexdigest()
        
        db_doc = Document(
            title=doc_title,
            source_url=doc_url,
            file_type=file_type,
            content_hash=content_hash
        )
        session.add(db_doc)
        await session.flush() # Get ID
        
        # Chunking
        chunks = self.text_splitter.create_documents([doc_content])
        
        # Create Chunk records
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding_vector = await self.embeddings.aembed_query(chunk.page_content)
            
            db_chunk = DocumentChunk(
                document_id=db_doc.id,
                chunk_index=i,
                content=chunk.page_content,
                embedding=embedding_vector,
                metadata_=chunk.metadata
            )
            session.add(db_chunk)
        
        await session.commit()
        return db_doc.id

    async def search(self, session: AsyncSession, query: str, limit: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for relevant chunks using vector similarity.
        """
        query_embedding = await self.embeddings.aembed_query(query)
        
        # Pgvector l2_distance or cosine_distance
        # Using l2_distance (<-> operator) or cosine distance (<=> operator)
        # SQLAlchemy pgvector support: DocumentChunk.embedding.l2_distance(query_embedding)
        
        # We need to manually calculate distance or use order_by with the operator
        # Using cosine distance <=>
        from sqlalchemy.orm import selectinload
        
        stmt = select(DocumentChunk).options(selectinload(DocumentChunk.document)).order_by(
            DocumentChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await session.execute(stmt)
        chunks = result.scalars().all()
        return chunks

    async def generate_response(self, question: str, chunks: List[DocumentChunk]) -> str:
        """
        Generate answer using LLM and retrieved chunks.
        """
        # Fetch document titles for context
        # Ideally we join Document in the search query, but for now we have chunks. 
        # The chunks have document_id. We might need to eager load document in search.
        
        context_parts = []
        for chunk in chunks:
            # We assume chunk.document is loaded or we load it. 
            # For Phase 1 we might skip explicit citation logic in the prompt construction if lazy loading fails, 
            # but let's try to assume it's available or we need to Modify search to join.
            content = chunk.content
            context_parts.append(content)
        
        context_text = "\n\n".join(context_parts)
        
        system_prompt = """You are Acture Advisor, an internal knowledge assistant.
Answer the question based ONLY on the following context.
If the answer is not in the context, say "I don't have information about that in our documentation".
Always cite your sources by referring to the document titles provided in the context.
"""
        user_prompt = f"""Context:
{context_text}

Question: {question}
Answer:"""

        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content


rag_service = RAGService()
