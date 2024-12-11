#!/bin/bash
set -e

echo "Starting application initialization..."

# Function to check if database is ready
check_db() {
    python scripts/setup_db.py
    return $?
}

# Wait for database to be ready
echo "Waiting for database..."
max_retries=30
retry_count=0
retry_delay=2

while [ $retry_count -lt $max_retries ]; do
    if check_db; then
        echo "Database setup completed successfully"
        break
    fi
    
    retry_count=$((retry_count + 1))
    
    if [ $retry_count -eq $max_retries ]; then
        echo "Database setup failed after $max_retries attempts"
        exit 1
    fi
    
    echo "Attempt $retry_count of $max_retries failed, retrying in $retry_delay seconds..."
    sleep $retry_delay
done

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 