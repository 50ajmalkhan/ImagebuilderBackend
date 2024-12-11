# AI Image/Video Generation API

A FastAPI-based backend service for generating images and videos using AI models (DALL-E and RunwayML).

## Features

- User authentication with Supabase
- Image generation using DALL-E
- Video generation using RunwayML
- Content storage in Supabase
- Generation history tracking
- RESTful API with OpenAPI documentation

## Prerequisites

- Python 3.8+
- Supabase account
- OpenAI API key
- RunwayML API key

## Project Structure

```
ImageBuilderBackend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py
│   │           └── generation.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── generation.py
│   └── services/
│       ├── __init__.py
│       ├── dalle_service.py
│       └── runway_service.py
├── scripts/
│   ├── init_db.py
│   └── migrations.py
├── tests/
│   ├── conftest.py
│   └── test_auth.py
├── requirements.txt
├── .env
└── README.md
```

## Setup

### Option 1: Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ImageBuilderBackend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your credentials:
```env
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# JWT Configuration
JWT_SECRET=your-jwt-secret

# AI Model Configuration
AI_MODEL_KEY=your-openai-api-key
RUNWAY_API_KEY=your-runway-api-key

# Storage Configuration
STORAGE_BUCKET=images

# Database Configuration
DB_HOST=your-supabase-host
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_NAME=postgres
```

5. Set up the database:
```bash
# Initialize the database with tables and migrations
python scripts/setup_db.py
```

### Option 2: Docker Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ImageBuilderBackend
```

2. Create `.env` file with your credentials (see Environment Variables section)

3. Build and start the containers:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## Running the Application

### Local Development
```bash
uvicorn app.main:app --reload
```

### Docker Production
```bash
docker-compose up -d
```

To view logs:
```bash
docker-compose logs -f
```

To stop the service:
```bash
docker-compose down
```

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - User login

### Generation

- `POST /api/v1/generation/generate-image` - Generate image from prompt
- `POST /api/v1/generation/generate-video` - Generate video from prompt
- `GET /api/v1/generation/history` - Get user's generation history

## Environment Variables

| Variable | Description |
|----------|-------------|
| SUPABASE_URL | Your Supabase project URL |
| SUPABASE_KEY | Your Supabase API key |
| JWT_SECRET | Secret key for JWT tokens |
| AI_MODEL_KEY | OpenAI API key for DALL-E |
| RUNWAY_API_KEY | RunwayML API key |
| STORAGE_BUCKET | Supabase storage bucket name |

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Security

- JWT-based authentication
- CORS protection
- Environment variable configuration
- Secure password hashing
- API key protection

## Database Management

### Creating New Migrations

To create a new migration after modifying models:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

To apply all pending migrations:
```bash
alembic upgrade head
```

### Rolling Back Migrations

To roll back the last migration:
```bash
alembic downgrade -1
```

## Docker Commands

### Building the Image
```bash
docker build -t image-generation-api .
```

### Running the Container
```bash
docker run -p 8000:8000 --env-file .env image-generation-api
```

### Cleaning Up
```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove unused images
docker system prune -a
```