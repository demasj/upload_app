# Local Development Setup Guide

This guide will help you set up your local development environment for the Large File Upload API.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- Virtual environment tool (virtualenv or venv)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd upload_app
```

### 2. Set Up Python Environment with pyenv

```bash
# Install Python 3.11 with pyenv
pyenv install 3.11.0

# Set local Python version
pyenv local 3.11.0

# Verify
python --version
```

### 3. Create Virtual Environment

Using `virtualenv` (recommended):

```bash
# Install virtualenv if not already installed
pip install virtualenv

# Create virtual environment
virtualenv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.local .env
```

Or manually create `.env` with:

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
AZURE_STORAGE_CONTAINER_NAME=uploads
REDIS_HOST=localhost
REDIS_PORT=6379
HOST=0.0.0.0
PORT=8000
```

### 6. Start Local Services with Docker Compose

```bash
# Start Redis and Azurite (local Azure Storage emulator)
docker-compose -f docker-compose.local.yml up -d

# Or start with logs visible
docker-compose -f docker-compose.local.yml up
```

Services started:
- **Azurite** (Azure Storage emulator): http://127.0.0.1:10000
- **Redis**: localhost:6379

### 7. Run the Application

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run FastAPI development server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc

## Project Structure

```
upload_app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── storage.py           # Storage backend (FileStorage, RedisStorage)
│   └── azure_handler.py     # Azure Blob Storage handler
├── frontend/
│   └── index.html           # Frontend application
├── config/                  # Configuration files
├── docker-compose.yml       # Production Docker Compose
├── docker-compose.local.yml # Local development Docker Compose
├── Dockerfile               # Docker image configuration
├── requirements.txt         # Python dependencies
└── .env.local              # Local environment template
```

## Development Workflow

### Testing the API

```bash
# Using curl
curl -X POST http://localhost:8000/api/config

# Or use the built-in test script
bash test_api.sh
```

### Running Tests

```bash
# Install test dependencies if needed
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code with Black
pip install black
black backend/

# Lint with Pylint
pip install pylint
pylint backend/

# Type checking with mypy
pip install mypy
mypy backend/
```

## Managing Services

### View Running Containers

```bash
docker-compose -f docker-compose.local.yml ps
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.local.yml logs -f

# Specific service
docker-compose -f docker-compose.local.yml logs -f azurite
docker-compose -f docker-compose.local.yml logs -f redis
```

### Stop Services

```bash
docker-compose -f docker-compose.local.yml down
```

### Stop Services and Remove Data

```bash
docker-compose -f docker-compose.local.yml down -v
```

## Troubleshooting

### Import Errors in VS Code

1. Select the correct Python interpreter:
   - Use **Python: Select Interpreter** command
   - Choose `.venv/bin/python`

2. Reload VS Code window:
   - Press `Ctrl+Shift+P` and type "Reload Window"

### Port Already in Use

If ports are already in use, either:

```bash
# Kill existing process
lsof -ti:8000,6379,10000 | xargs kill -9

# Or use different ports in docker-compose.local.yml
```

### Azurite Connection Issues

Ensure the connection string uses `127.0.0.1` (not `localhost`):

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;...;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure/Azurite connection string | See `.env.local` |
| `AZURE_STORAGE_CONTAINER_NAME` | Blob storage container name | `uploads` |
| `REDIS_HOST` | Redis server host | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `HOST` | FastAPI host binding | `0.0.0.0` |
| `PORT` | FastAPI port | `8000` |
| `CHUNK_SIZE` | Upload chunk size in bytes | `52428800` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `1099511627776` |

## Using Real Azure Storage (Production)

To switch from Azurite to real Azure Storage:

1. Create an Azure Storage Account (free tier available)
2. Get the connection string from Azure Portal
3. Update `.env`:
   ```env
   AZURE_STORAGE_CONNECTION_STRING=<your-real-connection-string>
   ```
4. Use production Docker Compose:
   ```bash
   docker-compose up
   ```

## Git Workflow

```bash
# Create a new feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature-name

# Create a Pull Request
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Azurite GitHub](https://github.com/Azure/Azurite)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Documentation](https://docs.docker.com/)

## Need Help?

- Check the main [README.md](../README.md)
- Review [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md)
- Check the [QUICKSTART.md](../QUICKSTART.md)
