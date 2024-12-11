import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import supabase
from app.core.config import get_settings
from supabase import create_client

settings = get_settings()

def init_database():
    try:
        # Create users table
        supabase.table("users").create({
            "id": "uuid references auth.users primary key",
            "full_name": "text",
            "email": "text unique",
            "created_at": "timestamp with time zone default timezone('utc'::text, now())"
        })

        # Create generation_logs table
        supabase.table("generation_logs").create({
            "id": "uuid default uuid_generate_v4() primary key",
            "user_id": "uuid references users(id)",
            "prompt": "text",
            "type": "text",
            "url": "text",
            "created_at": "timestamp with time zone default timezone('utc'::text, now())"
        })

        # Create storage bucket using service role key
        admin_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        try:
            admin_supabase.storage.get_bucket(settings.STORAGE_BUCKET)
            print(f"Storage bucket '{settings.STORAGE_BUCKET}' already exists")
        except Exception:
            try:
                admin_supabase.storage.create_bucket(settings.STORAGE_BUCKET, options={'public': True})
                print(f"Storage bucket '{settings.STORAGE_BUCKET}' created successfully")
            except Exception as e:
                print(f"Failed to create bucket: {str(e)}")

        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

if __name__ == "__main__":
    init_database() 