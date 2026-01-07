import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Acture Advisor 2.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "changethis"
    ENVIRONMENT: str = "development"
    
    # Database (Used for constructing URL if not provided directly, or unrelated usage)
    POSTGRES_USER: Optional[str] = "user"
    POSTGRES_PASSWORD: Optional[str] = "password"
    POSTGRES_DB: Optional[str] = "acture_advisor"
    DATABASE_URL: PostgresDsn
    
    # Auth
    AUTH_PROVIDER: str = "google" # or 'microsoft'
    
    # LLM
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OPENAI_API_KEY: Union[str, None] = None
    
    # Document Connectors
    SHAREPOINT_SITE_URL: Optional[str] = None
    AZURE_AD_CLIENT_ID: Optional[str] = None
    AZURE_AD_CLIENT_SECRET: Optional[str] = None
    AZURE_AD_TENANT_ID: Optional[str] = None
    
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore" # Important: Ignore unknown env vars to prevent startup crashes
    )

settings = Settings()
