# Development Guide - Large File Upload System

This comprehensive guide covers everything developers need to know about setting up, running, and extending the Large File Upload system.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend Development](#frontend-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Project Overview

A production-ready FastAPI application for uploading extremely large files (up to 1 TB) to Azure Blob Storage with resumable, chunked, and fault-tolerant capabilities.

**Key Components:**
- **Backend**: FastAPI server with 7 REST endpoints
- **Frontend**: Streamlit web interface
- **Storage**: Multiple backend options (Redis, file-based, etc.)
- **Azure Integration**: Block Blob API with SAS tokens

## 🏗️ Architecture

### System Components

```
┌─────────────┐    HTTP     ┌─────────────────┐
│  Streamlit  │◄──────────►│   FastAPI        │
│  Frontend   │            │   Backend        │
│  (Port 8501)│            │  (Port 8001)    │
└─────────────┘            └─────────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌──────▼─────┐   ┌──────▼─────┐  ┌─────▼────┐
            │  Storage    │   │ Azure Blob  │  │  Config   │
            │  Backend    │   │ Storage     │  │  Manager  │
            │ (Redis/File)│   │ API         │  │           │
            └─────────────┘   └─────────────┘  └───────────┘
```

### File Structure

```
upload_app/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── azure_handler.py    # Azure Blob Storage integration
│   ├── storage.py          # Storage backend abstraction
│   └── __pycache__/
├── frontend/               # Streamlit frontend
│   ├── app.py              # Main Streamlit app
│   ├── static/             # CSS, JS, HTML files
│   ├── Dockerfile          # Frontend container
│   └── requirements.txt
├── config/                 # Configuration management
│   ├── settings.py         # Pydantic settings
│   └── __pycache__/
├── tests/                  # Unit tests
├── uploads/                # Upload directory (local testing)
├── Dockerfile              # Backend container
├── docker-compose.local.yml # Local development with Azurite
├── docker-compose.yml      # Production deployment
├── requirements.txt        # Python dependencies
└── pytest.ini             # Test configuration
```

## 📋 Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for containerized development)
- **Git**
- **Azure Storage Account** (optional for local development)

### Optional Tools
- **pyenv** (Python version management)
- **virtualenv** (recommended over venv)
- **Azure CLI** (for Azure operations)

## 🚀 Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd upload_app
```

### 2. Python Environment Setup

#### Using pyenv (Recommended)

```bash
# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Verify version
python --version  # Should show 3.11.x
```

#### Create Virtual Environment

```bash
# Using virtualenv (recommended)
pip install virtualenv
virtualenv .venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration Setup

```bash
# Copy example configuration
cp config/.env.example config/.env

# Edit with your settings
nano config/.env
```

## ⚙️ Configuration

### Environment Variables

Create `config/.env` with the following variables:

```env
# Application Settings
DEBUG=true
HOST=0.0.0.0
PORT=8001

# Azure Storage (required for production)
AZURE_STORAGE_ACCOUNT_NAME=your_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_account_key
AZURE_STORAGE_CONTAINER_NAME=uploads

# Storage Backend (Redis recommended for production)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Upload Settings
CHUNK_SIZE=52428800        # 50MB chunks
MAX_FILE_SIZE=1099511627776 # 1TB max file size
MAX_CONCURRENT_UPLOADS=3   # Concurrent chunk uploads
```

### Docker Configuration

For Docker deployment, environment variables are set in `docker-compose.local.yml`:

```yaml
environment:
  - AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;...
  - REDIS_HOST=redis
  - CHUNK_SIZE=52428800
```

## 🏃 Running the Application

### Docker Development (Recommended)

```bash
# Start all services
docker-compose -f docker-compose.local.yml up --build

# Access points:
# Frontend: http://localhost:8501
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Local Development

#### Backend Only
```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server
python backend/main.py

# Server will be available at http://localhost:8001
```

#### Frontend Only
```bash
# Ensure backend is running on port 8001
cd frontend
streamlit run app.py

# Frontend will be available at http://localhost:8501
```

#### Full Stack (Separate Terminals)

Terminal 1 - Backend:
```bash
source .venv/bin/activate
python backend/main.py
```

Terminal 2 - Frontend:
```bash
cd frontend
source ../.venv/bin/activate  # or create separate venv
streamlit run app.py
```

## 📡 API Reference

### Base URL
```
http://localhost:8001/api
```

### Endpoints

#### Health Check
```http
GET /api/health
```

Returns system status and configuration.

#### Upload Configuration
```http
GET /api/config
```

Returns client-side configuration (chunk size, max file size).

#### Initialize Upload
```http
POST /api/upload/init
Content-Type: application/json

{
  "filename": "large-file.zip",
  "file_size": 1073741824
}
```

**Response:**
```json
{
  "upload_id": "abc123...",
  "chunk_size": 52428800,
  "total_chunks": 20
}
```

#### Upload Chunk
```http
POST /api/upload/chunk
Content-Type: multipart/form-data

Form Data:
- upload_id: abc123...
- chunk_index: 0
- file: <chunk_data>
```

#### Complete Upload
```http
POST /api/upload/complete
Content-Type: application/json

{
  "upload_id": "abc123..."
}
```

#### Get Upload Status
```http
GET /api/upload/status/{upload_id}
```

#### Resume Upload
```http
GET /api/upload/resume/{upload_id}
```

#### Cancel Upload
```http
DELETE /api/upload/{upload_id}
```

## 🌐 Frontend Development

### Streamlit App Structure

The frontend is built with Streamlit and consists of:

- `app.py`: Main application orchestrating components
- `static/styles.css`: UI styling
- `static/script.js`: Upload logic and API communication
- `static/template.html`: HTML structure

### Key Features

- **Memory-efficient**: Files are uploaded directly from browser
- **Progress tracking**: Real-time progress with speed indicators
- **Chunked uploads**: Automatic chunking for large files
- **Error handling**: User-friendly error messages

### Customization

#### Changing Upload Limits
Edit `frontend/app.py` or environment variables:

```python
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
```

#### Styling
Modify `frontend/static/styles.css` for UI changes.

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Structure

```
tests/
├── __init__.py
├── test_main.py       # API endpoint tests
├── test_config.py     # Configuration tests
├── test_storage.py    # Storage backend tests
├── test_azure_handler.py # Azure integration tests
```

### Writing Tests

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
```

## 🚢 Deployment

### Docker Production

```bash
# Build and run production containers
docker-compose up --build

# Scale services if needed
docker-compose up --scale app=3
```

### Environment Variables for Production

```env
DEBUG=false
AZURE_STORAGE_ACCOUNT_NAME=prod_account
AZURE_STORAGE_ACCOUNT_KEY=prod_key
REDIS_HOST=redis-cluster
```

### Azure Deployment

1. Create Azure Storage Account
2. Set environment variables
3. Deploy containers to Azure Container Instances or AKS
4. Configure Azure Front Door for CDN (optional)

## 🔧 Troubleshooting

### Common Issues

#### "Failed to fetch" Error
**Cause**: Frontend can't reach backend API
**Solution**: Check API_BASE in frontend environment (should be `http://localhost:8001`)

#### "Connection refused" to Redis
**Cause**: Redis service not running
**Solution**: 
```bash
# Start Redis
docker-compose -f docker-compose.local.yml up redis

# Or install locally
redis-server
```

#### Azure Container Creation Error
**Cause**: Container doesn't exist
**Solution**: The app auto-creates containers, but you can manually create:
```bash
az storage container create --name uploads --account-name your_account
```

#### Upload Hanging
**Cause**: Blocking Azure SDK calls
**Solution**: Ensure async operations use `asyncio.run_in_executor()`

### Debug Mode

Enable debug logging:

```env
DEBUG=true
```

Check logs:
```bash
# Docker logs
docker-compose logs -f app

# Local logs (visible in terminal)
```

### Health Checks

```bash
# API health
curl http://localhost:8001/api/health

# Container health
docker ps
```

## 📊 Monitoring

### Key Metrics

- Upload success/failure rates
- Average upload speed
- Chunk failure rates
- Storage backend performance

### Logging

Logs are output to:
- Docker: `docker-compose logs app`
- Local: Terminal output
- Files: Configure logging to files in production

## 🔒 Security Considerations

- Use SAS tokens for Azure access (not account keys in production)
- Implement authentication/authorization
- Validate file types and sizes
- Use HTTPS in production
- Regular security updates of dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Use type hints
- Write tests for new features
- Update documentation
- Follow PEP 8 style guide
- Use meaningful commit messages

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Blob Storage Docs](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

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
