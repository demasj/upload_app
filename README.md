# Large File Upload to Azure Blob Storage

A FastAPI-based web application that enables users to upload extremely large files (up to 1 TB) to Azure Blob Storage in a resumable, chunked, and fault-tolerant manner.

## Features

- 📤 **Chunked Uploads**: Break large files into manageable 50MB chunks
- 🔄 **Resumable Uploads**: Resume interrupted uploads from where they stopped
- 💾 **Multiple Storage Backends**: Redis, PostgreSQL, SQLite, or file-based storage for metadata
- 🚀 **Concurrent Chunk Uploads**: Upload multiple chunks simultaneously (default: 3 concurrent)
- 📊 **Real-time Progress**: Track upload progress in real-time
- 🔐 **Azure Block Blob API**: Uses stage_block + commit_block_list for reliability
- 🌐 **CORS Enabled**: Works with frontend and backend on different domains
- 📱 **Auto-Resume**: Automatically resume on connection loss (optional)

## System Architecture

```
┌─────────────┐
│  Frontend   │ (HTML/JS in /frontend)
│  (Browser)  │
└──────┬──────┘
       │
       │ HTTP/WebSocket
       │
┌──────▼──────────────────────┐
│   FastAPI Backend           │
│  /api/upload/*              │
│  - init                      │
│  - chunk                     │
│  - complete                  │
│  - status                    │
│  - resume                    │
│  - delete                    │
└──────┬──────────────────────┘
       │
       ├─────────────────┬──────────────────┐
       │                 │                  │
┌──────▼───┐    ┌────────▼─────┐   ┌──────▼─────┐
│  Storage  │    │Azure Blob    │   │   Config   │
│ Backend   │    │ Storage API  │   │ & Settings │
│(Redis/    │    │              │   │            │
│ File/DB)  │    │ stage_block  │   │            │
└───────────┘    │ commit_block │   └────────────┘
                 └──────────────┘
```

## Prerequisites

- Python 3.11+
- Virtual environment (.venv)
- **Optional**: Azure Storage Account (for production)
- **Optional**: Redis (for production, defaults to localhost for development)

## Installation

1. **Clone/Create project directory:**
```bash
cd /home/demas/Projects/upload_app
```

2. **Create virtual environment (if not exists):**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
Create `config/.env` with your settings:
```env
# App Settings
DEBUG=true
HOST=0.0.0.0
PORT=8001

# Azure Storage (optional for local development, required for production)
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_STORAGE_ACCOUNT_KEY=
AZURE_STORAGE_CONTAINER_NAME=uploads

# Redis (optional, defaults to localhost)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Upload Settings
CHUNK_SIZE=52428800
MAX_FILE_SIZE=1099511627776
```

## Running the Application

### Development Mode (Local)

```bash
cd /home/demas/Projects/upload_app
source .venv/bin/activate

# Run the backend
python backend/main.py
```

The API will be available at `http://localhost:8001`
- API docs: `http://localhost:8001/docs`
- Frontend: `http://localhost:8001/static/index.html`

**Note**: If port 8001 is already in use, either:
- Change `PORT` in `config/.env`
- Kill the existing process: `lsof -i :8001 && kill -9 <PID>`

### Production Mode

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker/Portainer Deployment

Since you're running Portainer, deploy using:
```bash
docker-compose up -d
```

The app runs on port 8001 locally, but can be configured differently in Docker Compose.

## API Endpoints

### 1. Initialize Upload
```
POST /api/upload/init
Content-Type: application/json

{
  "filename": "large_file.zip",
  "file_size": 1048576000
}

Response:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunk_size": 52428800,
  "message": "Upload initialized"
}
```

### 2. Upload Chunk
```
POST /api/upload/chunk
Content-Type: multipart/form-data

Parameters:
- upload_id: string
- chunk_index: integer
- file: binary chunk data

Response:
{
  "chunk_index": 0,
  "block_id": "base64_encoded_block_id",
  "progress_percentage": 5.5,
  "message": "Chunk uploaded successfully"
}
```

### 3. Complete Upload
```
POST /api/upload/complete
Content-Type: application/json

{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000"
}

Response:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "large_file.zip",
  "file_size": 1048576000,
  "blocks_count": 20,
  "message": "Upload completed successfully"
}
```

### 4. Get Upload Status
```
GET /api/upload/status/{upload_id}

Response:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "large_file.zip",
  "file_size": 1048576000,
  "chunk_size": 52428800,
  "block_ids": ["block_0", "block_1", ...],
  "progress_percentage": 45.0,
  "completed": false,
  "timestamp": "2024-11-22T10:30:00.000000"
}
```

### 5. Resume Upload
```
GET /api/upload/resume/{upload_id}

Response:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "large_file.zip",
  "file_size": 1048576000,
  "chunk_size": 52428800,
  "completed_chunks": 10,
  "block_ids": ["block_0", "block_1", ...],
  "progress_percentage": 50.0,
  "message": "Upload resumed"
}
```

### 6. Delete Upload
```
DELETE /api/upload/{upload_id}

Response:
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Upload deleted"
}
```

### 7. Get Configuration
```
GET /api/config

Response:
{
  "chunk_size": 52428800,
  "max_file_size": 1099511627776
}
```

## Frontend Features

### File Selection
- Drag & drop or click to select files
- Displays file size before upload

### Upload Progress
- Real-time progress percentage
- Bytes uploaded / total bytes
- Visual progress bar

### Resume Capability
- Auto-save upload ID to localStorage
- Auto-resume on connection loss (optional)
- Manual resume button available

### Error Handling
- Detailed error messages
- Graceful failure recovery
- Auto-retry for failed chunks (in advanced version)

## Storage Backend Options

### File-Based (Development)
Stores metadata in JSON files:
```python
from backend.storage import FileStorage
storage_backend = FileStorage(storage_dir=".uploads_state")
```

### Redis (Recommended for Production)
```python
import redis
from backend.storage import RedisStorage

redis_client = redis.asyncio.from_url("redis://localhost:6379/0")
storage_backend = RedisStorage(redis_client)
```

### PostgreSQL/SQLite (Advanced)
Create custom `StorageBackend` subclass implementing:
- `save_metadata()`
- `get_metadata()`
- `delete_metadata()`
- `add_block_id()`
- `get_block_ids()`
- `mark_completed()`

## Configuration

Edit `config/config.py` or `config/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_STORAGE_ACCOUNT_NAME` | (empty) | Azure storage account name |
| `AZURE_STORAGE_ACCOUNT_KEY` | (empty) | Azure storage account key |
| `AZURE_STORAGE_CONTAINER_NAME` | uploads | Container name |
| `CHUNK_SIZE` | 52428800 | Chunk size in bytes (50MB) |
| `MAX_FILE_SIZE` | 1099511627776 | Max file size (1TB) |
| `REDIS_HOST` | localhost | Redis hostname |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_DB` | 0 | Redis database number |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8001 | Server port (use 8001 to avoid conflicts with Portainer) |
| `DEBUG` | true | Debug mode (set to false in production) |

## Project Structure

```
upload_app/
├── backend/
│   ├── main.py              # FastAPI application & routes
│   ├── config.py            # Configuration management
│   ├── storage.py           # Storage backends
│   └── azure_handler.py     # Azure Blob Storage API handler
├── frontend/
│   └── index.html           # Single-page web interface
├── config/
│   ├── settings.py          # Base settings
│   └── .env                 # Environment variables (local dev)
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── .venv/                  # Virtual environment
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or change PORT in config/.env
```

### Import Errors
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### Azure Connection Error
- Add Azure credentials to `config/.env` (leave empty for local dev)
- Verify network connectivity to Azure
- Ensure container exists in your Azure account

### Upload Fails Midway
- Browser auto-resumes if `autoResume` is checked
- Click "Resume Upload" button manually
- Upload ID is saved in localStorage

### Progressive Upload Speed Decrease
- Reduce concurrent chunks: `CONCURRENT_CHUNKS = 3` in `frontend/index.html`
- Increase chunk size: `CHUNK_SIZE=104857600` (100MB) in `.env`

## Advanced Features (Future)

- [ ] Compression before upload
- [ ] Parallel multi-connection uploads
- [ ] Server-side chunk retry logic
- [ ] PostgreSQL metadata storage
- [ ] Web3 integration for decentralized storage
- [ ] Download tracking dashboard
- [ ] Virus scanning integration

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Max file size | 1 TB |
| Chunk size | 50 MB (configurable) |
| Concurrent uploads | 3 (configurable) |
| Typical speed | 50-100 MB/s (network dependent) |

## License

MIT

## Support

For issues or questions, create an issue in the repository or contact the development team.
