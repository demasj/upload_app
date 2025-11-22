# Quick Start Guide

## 5-Minute Setup

### 1. Activate Virtual Environment
```bash
cd /home/demas/Projects/upload_app
source .venv/bin/activate
```

### 2. Configure Azure Credentials
```bash
# Edit the .env file with your Azure details
nano config/.env
```

**Required fields:**
```env
AZURE_STORAGE_ACCOUNT_NAME=myaccount
AZURE_STORAGE_ACCOUNT_KEY=your_account_key_here
AZURE_STORAGE_CONTAINER_NAME=uploads
```

### 3. Run the Backend
```bash
python backend/main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Open Frontend
Open your browser to:
```
http://localhost:8000/static/index.html
```

### 5. Upload a File

1. **Select** a file using the file picker
2. **Click** "Start Upload"
3. **Wait** for progress to reach 100%
4. **Success!** File is now in Azure Blob Storage

## Testing with curl

### Initialize Upload
```bash
curl -X POST http://localhost:8000/api/upload/init \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.zip",
    "file_size": 1048576000
  }'
```

### Get Configuration
```bash
curl http://localhost:8000/api/config
```

### Check Upload Status
```bash
curl http://localhost:8000/api/upload/status/{upload_id}
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Make sure venv is activated
source .venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### "Connection refused" to Azure
- Check `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY` in `.env`
- Verify your Azure account is accessible
- Check network connectivity

### Frontend not loading
- Make sure backend is running: `python backend/main.py`
- Check if port 8000 is accessible
- Try: `http://localhost:8000/api/config` to verify backend

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| AZURE_STORAGE_ACCOUNT_NAME | ✅ Yes | - |
| AZURE_STORAGE_ACCOUNT_KEY | ✅ Yes | - |
| AZURE_STORAGE_CONTAINER_NAME | No | uploads |
| CHUNK_SIZE | No | 52428800 (50MB) |
| MAX_FILE_SIZE | No | 1099511627776 (1TB) |
| REDIS_HOST | No | localhost |
| REDIS_PORT | No | 6379 |
| HOST | No | 0.0.0.0 |
| PORT | No | 8000 |
| DEBUG | No | False |

## File Upload Limits

- **Chunk Size**: 50 MB (configurable in .env)
- **Max File Size**: 1 TB (configurable in .env)
- **Concurrent Chunks**: 3 (configurable in frontend/index.html)

## Storage Options

### Development (File-based - Default)
Metadata stored in `.uploads_state/` directory

### Production (Redis - Recommended)
Set up Redis first:
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Then update REDIS_HOST and REDIS_PORT in .env
```

## Next Steps

1. **Customize chunk size** for your network:
   - Slow network: 10-20 MB chunks
   - Fast network: 100-200 MB chunks

2. **Set up Redis** for production:
   ```bash
   docker-compose up -d
   ```

3. **Deploy with Docker**:
   ```bash
   docker build -t upload-app .
   docker run -p 8000:8000 upload-app
   ```

4. **Monitor uploads** via API:
   ```bash
   curl http://localhost:8000/api/upload/status/{upload_id}
   ```

## API Documentation

When the app is running, visit:
```
http://localhost:8000/docs
```

This will show interactive API documentation with try-it-out functionality.
