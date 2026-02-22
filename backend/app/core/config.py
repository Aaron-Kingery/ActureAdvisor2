import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Acture Advisor 2.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "changethis"
    ENVIRONMENT: str = "development"
    
    # Database
    POSTGRES_USER: Optional[str] = "user"
    POSTGRES_PASSWORD: Optional[str] = "password"
    POSTGRES_DB: Optional[str] = "acture_advisor"
    DATABASE_URL: PostgresDsn
    
    # Auth provider (legacy, kept for compat)
    AUTH_PROVIDER: str = "microsoft"
    
    # Platform SSO (Entra ID — "Acture Platform" app registration)
    PLATFORM_CLIENT_ID: Optional[str] = None
    PLATFORM_CLIENT_SECRET: Optional[str] = None
    PLATFORM_REDIRECT_URI: str = "https://advisor.acture.ai/auth/callback"
    SESSION_SECRET: str = "change-this-session-secret"
    USER_PROFILE_SERVICE_URL: Optional[str] = None
    
    # Azure AD (Service Principal — for SharePoint sync)
    AZURE_AD_CLIENT_ID: Optional[str] = None
    AZURE_AD_CLIENT_SECRET: Optional[str] = None
    AZURE_AD_TENANT_ID: Optional[str] = None
    
    # LLM
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OPENAI_API_KEY: Union[str, None] = None
    
    # Document Connectors
    SHAREPOINT_SITE_URL: Optional[str] = None
    
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
