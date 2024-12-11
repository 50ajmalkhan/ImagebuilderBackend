import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import supabase

def run_migrations():
    try:
        # Create indexes for better query performance
        supabase.rpc('create_index', {
            'table_name': 'users',
            'index_name': 'users_email_idx',
            'column_name': 'email'
        }).execute()

        supabase.rpc('create_index', {
            'table_name': 'generation_logs',
            'index_name': 'generation_logs_user_id_idx',
            'column_name': 'user_id'
        }).execute()

        supabase.rpc('create_index', {
            'table_name': 'generation_logs',
            'index_name': 'generation_logs_created_at_idx',
            'column_name': 'created_at'
        }).execute()

        # Add any future migrations here

        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {str(e)}")

if __name__ == "__main__":
    run_migrations() 