import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
import os

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_settings():
    # Override settings for testing
    os.environ["SUPABASE_URL"] = "test_url"
    os.environ["SUPABASE_KEY"] = "test_key"
    os.environ["JWT_SECRET"] = "test_secret"
    os.environ["AI_MODEL_KEY"] = "test_ai_key"
    os.environ["RUNWAY_API_KEY"] = "test_runway_key"
    os.environ["STORAGE_BUCKET"] = "test_images"
    
    return get_settings() 