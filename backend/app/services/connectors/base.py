from abc import ABC, abstractmethod
from typing import List, Optional, BinaryIO, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DocumentMetadata:
    source_id: str
    title: str
    source_url: str
    file_type: str
    created_at: datetime
    updated_at: datetime
    content_hash: Optional[str] = None

class DocumentConnector(ABC):
    @abstractmethod
    async def list_documents(self) -> AsyncGenerator[DocumentMetadata, None]:
        """List available documents from the source."""
        pass

    @abstractmethod
    async def get_document_content(self, source_id: str) -> BinaryIO:
        """Retrieve the raw content of a document."""
        pass
