import os
from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Acture Advisor 2.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "changethis"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: PostgresDsn
    
    # Auth
    AUTH_PROVIDER: str = "google" # or 'microsoft'
    
    # LLM
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OPENAI_API_KEY: Union[str, None] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
