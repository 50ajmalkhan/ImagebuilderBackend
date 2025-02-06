from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List, Union
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )
    
    PROJECT_NAME: str = "VidGen API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # JWT settings
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Email verification settings
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    
    # AI Model settings
    AI_MODEL_KEY: str
    RUNWAY_API_KEY: str
    
    # Database settings
    DB_HOST: str
    DB_PORT: Union[str, int] = "5432"
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Mailjet settings
    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    
    # Frontend URL for email verification
    FRONTEND_URL: str

    # S3 Storage Settings
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "ap-southeast-1"
    S3_ENDPOINT: str
    
    # Stripe Settings
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

@lru_cache()
def get_settings() -> Settings:
    return Settings() 