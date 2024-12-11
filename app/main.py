from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1.endpoints import auth, generation
from app.db.session import engine, supabase
import psutil
import os

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(generation.router, prefix=f"{settings.API_V1_STR}/generation", tags=["Generation"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Image/Video Generation API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "services": {
            "database": "unhealthy",
            "supabase": "unhealthy"
        },
        "system": {
            "cpu_usage": f"{psutil.cpu_percent()}%",
            "memory_usage": f"{psutil.virtual_memory().percent}%",
            "disk_usage": f"{psutil.disk_usage('/').percent}%"
        }
    }

    try:
        # Test database connection
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = str(e)

    try:
        # Test Supabase connection
        supabase.auth.get_user("test")
    except Exception:
        # Expected to fail with invalid token, but connection works
        health_status["services"]["supabase"] = "healthy"

    # Overall status
    if all(status == "healthy" for status in health_status["services"].values()):
        health_status["status"] = "healthy"
    else:
        health_status["status"] = "degraded"
        return health_status, status.HTTP_503_SERVICE_UNAVAILABLE

    return health_status 