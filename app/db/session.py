from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import boto3
from botocore.config import Config

settings = get_settings()

# Create SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure S3 client with increased timeouts and retries
config = Config(
    retries=dict(max_attempts=3),
    connect_timeout=300,  # 5 minutes
    read_timeout=300,
    max_pool_connections=50,
    signature_version='s3v4'  # Use signature v4 for Supabase
)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION,
    endpoint_url=settings.S3_ENDPOINT,
    config=config
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 