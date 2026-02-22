from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from app.core.config import settings

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.embeddings = OllamaEmbeddings(
            base_url=self.base_url,
            model="nomic-embed-text"
        )
        self.llm = ChatOllama(
            base_url=self.base_url,
            model="llama3.2:3b",
            temperature=0.1,
            num_ctx=4096
        )

    def get_embeddings(self):
        return self.embeddings

    def get_llm(self):
        return self.llm

ollama_service = OllamaService()
