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
    
    PROJECT_NAME: str = "AI Image/Video Generation API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT settings
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Model settings
    AI_MODEL_KEY: str
    RUNWAY_API_KEY: str
    
    # Storage settings
    STORAGE_BUCKET: str = "images"
    
    # Database settings
    DB_HOST: str
    DB_PORT: Union[str, int] = "6543"
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

@lru_cache()
def get_settings() -> Settings:
    return Settings() 