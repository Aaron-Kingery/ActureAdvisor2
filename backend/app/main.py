from fastapi import FastAPI
from app.core.config import settings
from app.api.api_v1.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
)

from fastapi.middleware.cors import CORSMiddleware

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
from app.api.api_v1.endpoints import chat
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

