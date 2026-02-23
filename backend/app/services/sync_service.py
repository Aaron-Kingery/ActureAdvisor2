import hashlib
import traceback
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
            logger.info("Scanning documents from source...")
            
            result = await self.session.execute(select(Document))
            db_docs = result.scalars().all()
            # Extract plain Python values to avoid ORM lazy-load after rollback
            db_id_map = {doc.source_url: doc.id for doc in db_docs}
            db_hash_map = {doc.source_url: doc.content_hash for doc in db_docs}
            
            current_urls = set()
            processed_count = 0
            
            async for meta in connector.list_documents():
                current_urls.add(meta.source_url)
                
                try:
                    existing_id = db_id_map.get(meta.source_url)
                    if existing_id:
                        existing_hash = db_hash_map.get(meta.source_url)
                        if meta.content_hash and meta.content_hash == existing_hash:
                             continue
                        
                        logger.info(f"Updating document: {meta.title}")
                        await self._process_document(connector, meta, existing_id=existing_id)
                    else:
                        logger.info(f"New document found: {meta.title}")
                        await self._process_document(connector, meta)
                    
                    await self.session.commit()
                    processed_count += 1
                    
                except Exception as doc_err:
                    logger.error(f"Failed to process document {meta.title} ({meta.source_url}): {doc_err}")
                    await self.session.rollback()
                    continue

            # Handle deletions
            for url, doc_id in db_id_map.items():
                if url not in current_urls:
                    logger.info(f"Deleting removed document (id={doc_id})")
                    doc = await self.session.get(Document, doc_id)
                    if doc:
                        await self.session.delete(doc)
            
            await self.session.commit()
            logger.info(f"Sync completed. Processed {processed_count} documents.")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            await self.session.flush()  # Get ID

        # Chunk and Embed
        logger.info(f"Chunking and embedding {meta.title}...")
        await self.rag_service.process_document(doc, content_text, self.session)
