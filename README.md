# AI Image/Video Generation API

A FastAPI-based service for generating images and videos using AI models.

## Features
- User authentication with JWT
- Image generation using DALL-E
- Video generation using Runway ML
- Content storage in S3
- Token-based usage tracking
- Email verification

## Prerequisites
- Python 3.11+
- PostgreSQL database
- S3-compatible storage
- Mailjet account
- OpenAI API key
- Runway ML API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ImagebuilderBackend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Database Configuration
DB_HOST=your-db-host
DB_PORT=5432
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name

# JWT Configuration
JWT_SECRET=your-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Email Settings (Mailjet)
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_SECRET_KEY=your-mailjet-secret-key
MAIL_FROM=your-sender-email
MAIL_FROM_NAME=Your Sender Name
VERIFICATION_TOKEN_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:5173

# AI Model Configuration
AI_MODEL_KEY=your-openai-api-key
RUNWAY_API_KEY=your-runway-api-key

# S3 Storage Settings
S3_ACCESS_KEY=your-s3-access-key
S3_SECRET_KEY=your-s3-secret-key
S3_BUCKET_NAME=your-bucket-name
S3_REGION=your-region
S3_ENDPOINT=your-s3-endpoint

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_HOST | API host address |
| API_PORT | API port number |
| DEBUG | Debug mode flag |
| DB_HOST | Database host address |
| DB_PORT | Database port |
| DB_USER | Database username |
| DB_PASSWORD | Database password |
| DB_NAME | Database name |
| JWT_SECRET | Secret key for JWT |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token expiration time |
| ALGORITHM | JWT algorithm |
| MAILJET_API_KEY | Mailjet API key |
| MAILJET_SECRET_KEY | Mailjet secret key |
| MAIL_FROM | Sender email address |
| MAIL_FROM_NAME | Sender name |
| VERIFICATION_TOKEN_EXPIRE_HOURS | Email verification token expiration |
| FRONTEND_URL | Frontend application URL |
| AI_MODEL_KEY | OpenAI API key |
| RUNWAY_API_KEY | Runway ML API key |
| S3_ACCESS_KEY | S3 access key |
| S3_SECRET_KEY | S3 secret key |
| S3_BUCKET_NAME | S3 bucket name |
| S3_REGION | S3 region |
| S3_ENDPOINT | S3 endpoint URL |
| ALLOWED_ORIGINS | CORS allowed origins |
| LOG_LEVEL | Logging level |

## Running with Docker

1. Build and start the containers:
```bash
docker-compose up --build -d
```

2. The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation at `http://localhost:8000/docs`
- ReDoc documentation at `http://localhost:8000/redoc`

## Development

1. Run migrations:
```bash
alembic upgrade head
```

2. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run tests with:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.