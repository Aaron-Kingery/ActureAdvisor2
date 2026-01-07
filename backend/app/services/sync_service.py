import hashlib
from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk
from app.services.connectors.base import DocumentConnector
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
import logging

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, session: AsyncSession, rag_service: RAGService):
        self.session = session
        self.rag_service = rag_service

    async def sync_connector(self, connector: DocumentConnector):
        """
        Synchronizes documents from a given connector.
        """
        try:
            # 1. List documents from source
            logger.info("Fetching document list from source...")
            source_docs = await connector.list_documents()
            logger.info(f"Found {len(source_docs)} documents in source.")

            # 2. Get existing documents from DB
            result = await self.session.execute(select(Document))
            db_docs = result.scalars().all()
            db_docs_map = {doc.source_url: doc for doc in db_docs}
            
            # 3. Process each source document
            current_urls = set()
            
            for meta in source_docs:
                current_urls.add(meta.source_url)
                
                # Check if exists and if needs update
                if meta.source_url in db_docs_map:
                    existing = db_docs_map[meta.source_url]
                    # Simple change detection (timestamp or hash if available)
                    # For now, we'll assume if meta.content_hash allows check, else always update?
                    # Let's use simple timestamp logic if hash not provided
                    if meta.content_hash and meta.content_hash == existing.content_hash:
                         continue # No change
                    
                    logger.info(f"Updating document: {meta.title}")
                    await self._process_document(connector, meta, existing_id=existing.id)
                else:
                    logger.info(f"New document found: {meta.title}")
                    await self._process_document(connector, meta)

            # 4. Handle Deletions
            for url, doc in db_docs_map.items():
                if url not in current_urls:
                    logger.info(f"Deleting document: {doc.title}")
                    await self.session.delete(doc) # Cascade should handle chunks?
            
            await self.session.commit()
            logger.info("Sync completed.")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            await self.session.rollback()
            raise

    async def _process_document(self, connector: DocumentConnector, meta, existing_id=None):
        # Download
        content_stream = await connector.get_document_content(meta.source_id)
        
        # Extract Text
        content_text = DocumentProcessor.extract_text(content_stream, meta.file_type)
        
        # Calculate Hash
        content_hash = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
        
        # Delete existing chunks if updating
        if existing_id:
            doc = await self.session.get(Document, existing_id)
            doc.title = meta.title
            doc.content_hash = content_hash
            doc.last_synced = meta.updated_at
            
            # Remove old chunks
            await self.session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == existing_id))
        else:
            doc = Document(
                source_url=meta.source_url,
                title=meta.title,
                file_type=meta.file_type,
                content_hash=content_hash,
                last_synced=meta.updated_at
            )
            self.session.add(doc)
            await self.session.flush() # Get ID

        # Chunk and Embed
        logger.info(f"Chunking and embedding {meta.title}...")
        await self.rag_service.process_document(doc, content_text, self.session)
