from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1.endpoints import auth, generation, token, subscription
from app.db.session import engine, s3_client
import psutil
import os

settings = get_settings()

app = FastAPI(
    title="VidGen API",
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
app.include_router(token.router, prefix=f"{settings.API_V1_STR}/tokens", tags=["Tokens"])
app.include_router(subscription.router, prefix=f"{settings.API_V1_STR}/subscription", tags=["Subscriptions"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to VidGen API",
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
            "storage": "unhealthy"
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
        # Test S3 connection
        s3_client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, MaxKeys=1)
        health_status["services"]["storage"] = "healthy"
    except Exception as e:
        health_status["services"]["storage"] = str(e)

    # Overall status
    if all(status == "healthy" for status in health_status["services"].values()):
        health_status["status"] = "healthy"
    else:
        health_status["status"] = "degraded"
        return health_status, status.HTTP_503_SERVICE_UNAVAILABLE

    return health_status 