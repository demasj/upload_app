# Docker Configuration Guide for upload_app

This guide verifies that all Docker settings, credentials, and port numbers are correctly configured for running with `docker-compose.local.yml`.

## Quick Verification Checklist

### 1. Run Health Check Endpoint
After starting docker-compose, verify everything is working:

```bash
curl http://localhost:8001/api/health
```

This will show:
- ✓ App is running
- ✓ Azure Storage configuration (using Azurite emulator)
- ✓ Redis configuration
- ✓ Chunk size and file size limits

### 2. Port Mappings

| Service | Container Port | Host Port | Purpose |
|---------|---|---|---|
| **app** | 8000 | 8001 | FastAPI server |
| **redis** | 6379 | 6379 | Cache/session store |
| **azurite** | 10000 | 10000 | Blob Storage |
| **azurite** | 10001 | 10001 | Queue Service |
| **azurite** | 10002 | 10002 | Table Service |

### 3. Environment Variables

#### docker-compose.local.yml (Docker network)
```yaml
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;
AZURE_STORAGE_CONTAINER_NAME=uploads
REDIS_HOST=redis
REDIS_PORT=6379
CHUNK_SIZE=52428800      # 50MB
MAX_FILE_SIZE=1099511627776  # 1TB
```

#### .env.local (Local development without Docker)
```dotenv
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
AZURE_STORAGE_CONTAINER_NAME=uploads
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Key Differences

**Docker Network:** Uses service names (`azurite:10000`, `redis:6379`)
- Services communicate internally on the `upload_network` bridge

**Local Development:** Uses localhost (`127.0.0.1:10000`, `localhost:6379`)
- Services must be running on your machine

## Azure Storage Credentials (Azurite Emulator)

**Account Name:** `devstoreaccount1`
**Account Key:** `Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==`
**Container:** `uploads`

These are the **default Azurite credentials** - they work with the emulator only.

## Starting the Application

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.local.yml up --build

# Check logs
docker-compose -f docker-compose.local.yml logs -f app

# Stop services
docker-compose -f docker-compose.local.yml down
```

## Troubleshooting

### Error: "The specified container does not exist"
**Cause:** Azurite container needs to be created before uploading
**Solution:** The app now **automatically creates the `uploads` container** on startup if it doesn't exist. If you see this error:
1. Rebuild the image: `docker-compose -f docker-compose.local.yml down && docker-compose -f docker-compose.local.yml up --build`
2. Check logs for container creation: `docker-compose -f docker-compose.local.yml logs app | grep -i "container"`
3. Manually create container (if needed): 
   ```bash
   docker exec upload_app-app-1 python -c "from config import get_settings; from backend.azure_handler import AzureBlobHandler; h = AzureBlobHandler(get_settings()); h._ensure_container_exists()"
   ```

### Error: "Connection refused" to Redis
**Cause:** REDIS_HOST is set to `localhost` instead of `redis` service name
**Solution:** Verify docker-compose sets `REDIS_HOST=redis`

### Error: "Connection refused" to Azurite
**Cause:** Service not running or port not exposed correctly
**Solution:** 
1. Verify Azurite container is running: `docker-compose -f docker-compose.local.yml ps`
2. Check port 10000 is exposed: `docker ps | grep azurite`
3. Test connection: `curl http://127.0.0.1:10000/` (should fail with auth error, but proves connectivity)

### Upload hanging
**Cause:** Blocking Azure SDK calls not running in thread pool
**Solution:** Verified - `stage_block()` and `commit_block_list()` now use `asyncio.run_in_executor()`

## API Endpoints

### Health Check (Configuration Diagnostic)
```bash
GET /api/health
```
Returns full configuration including:
- Azure Storage status (configured, using Azurite, container name)
- Redis host/port
- Chunk size and file size limits

### Upload Config
```bash
GET /api/config
```
Returns client-side configuration:
- `chunk_size`: Size of each chunk (50MB)
- `max_file_size`: Maximum file size (1TB)

### Upload Endpoints
- `POST /api/upload/init` - Initialize upload session
- `POST /api/upload/chunk` - Upload a chunk
- `POST /api/upload/complete` - Finalize upload
- `GET /api/upload/resume/{upload_id}` - Resume incomplete upload
- `GET /api/upload/status/{upload_id}` - Get upload status
- `DELETE /api/upload/{upload_id}` - Cancel upload

## Configuration Flow

```
docker-compose.local.yml (environment variables)
        ↓
        config/settings.py (Settings class)
        ↓
        backend/main.py (uses get_settings())
        ↓
        backend/azure_handler.py (AzureBlobHandler)
        ↓
        Azure Blob Storage (Azurite emulator)
```

All configurations are validated at startup and logged for debugging.

## Next Steps

1. Verify health endpoint: `curl http://localhost:8001/api/health`
2. Open frontend: `http://localhost:8001`
3. Upload a test file
4. Check app logs for any errors: `docker-compose -f docker-compose.local.yml logs app`
