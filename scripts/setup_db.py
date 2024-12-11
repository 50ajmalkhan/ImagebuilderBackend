import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic import command
from app.db.session import engine
from sqlalchemy import text, inspect
from app.core.config import get_settings
from supabase import create_client

settings = get_settings()

def check_database_connection():
    """Check if database is accessible."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def check_if_tables_exist():
    """Check if the required tables already exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = ['users', 'generations']
    return all(table in existing_tables for table in required_tables)

def setup_storage_bucket():
    """Create or verify the storage bucket."""
    try:
        bucket_name = settings.STORAGE_BUCKET
        
        # Create a new Supabase client with service role key for admin operations
        admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        # Try to get bucket info (this will fail if bucket doesn't exist)
        try:
            admin_supabase.storage.get_bucket(bucket_name)
            print(f"Storage bucket '{bucket_name}' already exists")
            return True
        except Exception:
            # Bucket doesn't exist, create it
            try:
                admin_supabase.storage.create_bucket(bucket_name, options={'public': True})
                print(f"Storage bucket '{bucket_name}' created successfully")
                return True
            except Exception as e:
                print(f"Failed to create bucket: {str(e)}")
                return False
            
    except Exception as e:
        print(f"Error setting up storage bucket: {str(e)}")
        return False

def setup_database():
    """Set up the database and storage."""
    print("Starting database setup...")
    
    if check_if_tables_exist():
        print("Tables already exist, skipping migrations")
    else:
        print("Running database migrations...")
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            print("Database migrations completed successfully")
        except Exception as e:
            print(f"Error running migrations: {str(e)}")
            return False

    print("Setting up storage bucket...")
    if not setup_storage_bucket():
        print("Warning: Storage bucket setup failed")
        print("The application will continue, but file uploads may not work")
        print("Please check the Supabase storage permissions")
    
    print("Database setup completed successfully!")
    return True

if __name__ == "__main__":
    setup_database() 