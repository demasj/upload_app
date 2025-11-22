# 🎯 Getting Started - Large File Upload System

## Overview

You now have a **complete, production-ready** FastAPI application for uploading large files to Azure Blob Storage with resumable uploads and real-time progress tracking.

**Status**: ✅ **READY TO USE** (packages installed, structure complete)

---

## 🚀 Quick Start (2 Steps)

### Step 1: Configure Azure Credentials

Edit the `.env` file with your Azure Storage credentials:

```bash
nano config/.env
```

Update these fields with your actual Azure credentials:
```env
AZURE_STORAGE_ACCOUNT_NAME=your_actual_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_actual_account_key
AZURE_STORAGE_CONTAINER_NAME=uploads
```

### Step 2: Start the Server

```bash
# Option A: Use the startup script (auto-activates venv)
./start.sh

# Option B: Manual startup
source .venv/bin/activate
python backend/main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Open the Frontend

Open your browser to:
```
http://localhost:8000/static/index.html
```

**Done!** 🎉 Your application is running.

---

## 📁 What You Have

### Backend (Python - FastAPI)
- **main.py** - REST API with 7 endpoints
- **config.py** - Configuration management
- **storage.py** - Metadata storage (file/Redis backends)
- **azure_handler.py** - Azure SDK integration

### Frontend (HTML/JavaScript)
- **index.html** - Modern web UI with progress tracking, resume, auto-save

### Configuration
- **config/.env** - Your Azure credentials go here
- **config/.env.example** - Template

### Utilities
- **start.sh** - Auto-startup script
- **test_api.sh** - API testing script
- **verify.sh** - System verification script

### Documentation
- **README.md** - Full API & system documentation
- **QUICKSTART.md** - Quick reference
- **PROJECT_SUMMARY.md** - Complete project overview

### Deployment
- **Dockerfile** - Container image
- **docker-compose.yml** - Multi-service setup (app + Redis)
- **requirements.txt** - All dependencies (✅ already installed)

---

## 💡 Common Tasks

### Upload a File
1. Open: `http://localhost:8000/static/index.html`
2. Select a file
3. Click "Start Upload"
4. Watch progress in real-time
5. Auto-resumes on connection loss (optional)

### Check API Status
```bash
curl http://localhost:8000/api/config
```

### View API Documentation
```
http://localhost:8000/docs
```

### Test the API
```bash
./test_api.sh
```

### Verify Installation
```bash
./verify.sh
```

### Change Chunk Size
Edit `config/.env`:
```env
CHUNK_SIZE=104857600  # 100MB instead of 50MB
```

### Deploy with Docker
```bash
docker-compose up -d
```

---

## 🔧 Configuration

### Key Settings (config/.env)

| Setting | Default | Purpose |
|---------|---------|---------|
| `AZURE_STORAGE_ACCOUNT_NAME` | **REQUIRED** | Your Azure account |
| `AZURE_STORAGE_ACCOUNT_KEY` | **REQUIRED** | Your Azure key |
| `AZURE_STORAGE_CONTAINER_NAME` | uploads | Where files go |
| `CHUNK_SIZE` | 50 MB | Upload chunk size |
| `MAX_FILE_SIZE` | 1 TB | Maximum file size |
| `REDIS_HOST` | localhost | For production storage |
| `PORT` | 8000 | Server port |

---

## 📊 System Architecture

```
┌─────────────────────────────────────────┐
│        Browser (User Interface)          │
│        frontend/index.html              │
└──────────────┬──────────────────────────┘
               │ HTTP Requests
               ▼
┌─────────────────────────────────────────┐
│        FastAPI Backend (main.py)        │
│  ├─ POST /api/upload/init              │
│  ├─ POST /api/upload/chunk             │
│  ├─ POST /api/upload/complete          │
│  ├─ GET  /api/upload/status/{id}       │
│  ├─ GET  /api/upload/resume/{id}       │
│  ├─ DELETE /api/upload/{id}            │
│  └─ GET  /api/config                   │
└──────────────┬──────────────┬───────────┘
               │              │
    ┌──────────▼──┐    ┌──────▼──────────┐
    │   Storage   │    │ Azure Blob      │
    │  Backend    │    │ Storage API     │
    │ (File/Redis)│    │ (stage_block +  │
    └─────────────┘    │  commit_block)  │
                       └─────────────────┘
```

---

## 🧪 Testing

### Option 1: Browser Testing (Easiest)
1. Open: `http://localhost:8000/static/index.html`
2. Select any file
3. Click "Start Upload"

### Option 2: API Testing
```bash
# Test the API is running
curl http://localhost:8000/api/config

# Run the test script
./test_api.sh
```

### Option 3: curl Command
```bash
# Initialize upload
curl -X POST http://localhost:8000/api/upload/init \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.zip","file_size":1048576000}'

# Get upload status
curl http://localhost:8000/api/upload/status/{upload_id}
```

---

## ⚠️ Troubleshooting

### "Port 8000 already in use"
```bash
# Find what's using port 8000
lsof -i :8000

# Or use a different port
# Edit backend/main.py, change port in uvicorn.run()
```

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Activate the virtual environment
source .venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### "Connection refused" to Azure
1. Check credentials in `config/.env`
2. Verify Azure account exists and is accessible
3. Ensure container exists in Azure Storage

### "Frontend not loading"
1. Make sure backend is running: `python backend/main.py`
2. Try: `http://localhost:8000/api/config` - should return JSON
3. Check browser console for errors (F12)

---

## 🎓 Project Structure at a Glance

```
upload_app/
├── 📁 backend/          ← Python FastAPI code
│   ├── main.py         ← API endpoints
│   ├── config.py       ← Settings
│   ├── storage.py      ← Metadata storage
│   └── azure_handler.py ← Azure integration
│
├── 📁 frontend/         ← Web UI
│   └── index.html      ← Modern responsive interface
│
├── 📁 config/          ← Configuration
│   ├── .env            ← Your credentials (EDIT THIS!)
│   └── .env.example    ← Template
│
├── 📁 .venv/           ← Python packages (installed ✓)
│
├── 📋 *.sh            ← Helper scripts
│   ├── start.sh       ← Start the server
│   ├── test_api.sh    ← Test the API
│   └── verify.sh      ← Verify installation
│
├── 📖 *.md            ← Documentation
│   ├── README.md           ← Full reference
│   ├── QUICKSTART.md       ← Quick guide
│   └── PROJECT_SUMMARY.md  ← Overview
│
├── 🐳 Dockerfile      ← Container image
├── 🐳 docker-compose.yml ← Multi-service setup
└── 📄 requirements.txt ← Installed packages
```

---

## 🚀 Next Steps

### For Development
1. ✅ Complete: Setup and installation
2. ✅ Complete: Backend implementation
3. ✅ Complete: Frontend UI
4. ⏭️  **Your turn**: Add your Azure credentials to `.env`
5. ⏭️  **Your turn**: Run `./start.sh` to start server
6. ⏭️  **Your turn**: Open browser and upload files

### For Production
1. Get Azure credentials and update `.env`
2. Set up Redis for metadata storage (optional but recommended)
3. Deploy using Docker: `docker-compose up -d`
4. Set up HTTPS/SSL with reverse proxy (Nginx, Traefik)
5. Monitor uploads via `/api/upload/status/{id}`

### Advanced Customization
- Modify `CHUNK_SIZE` for your network speed
- Implement PostgreSQL backend (extend `StorageBackend` class)
- Add authentication/authorization
- Set up webhooks for upload completion
- Add compression before upload

---

## 📚 Documentation

### Quick References
- **README.md** - Complete API documentation and system overview
- **QUICKSTART.md** - 5-minute setup guide
- **PROJECT_SUMMARY.md** - Project details and architecture

### Interactive Docs (When Server Running)
```
http://localhost:8000/docs
```

This shows interactive Swagger API documentation where you can try endpoints.

---

## 💬 FAQ

**Q: Do I need Redis?**
A: No. File-based storage works for development. Redis is recommended for production (concurrent uploads).

**Q: What's the maximum file size?**
A: Configured to 1 TB (adjustable in `.env` with `MAX_FILE_SIZE`).

**Q: What happens if upload fails?**
A: Frontend auto-resumes from where it stopped. Upload ID is saved in browser localStorage.

**Q: Can I change chunk size?**
A: Yes. Edit `CHUNK_SIZE` in `config/.env` (default 50MB). Must be 4-100MB.

**Q: How do I deploy to production?**
A: Use Docker: `docker-compose up -d` (see docker-compose.yml)

**Q: Is authentication required?**
A: No, but you can add it in backend/main.py using FastAPI's built-in auth.

---

## 🎯 You're All Set!

Everything is configured and ready. Just add your Azure credentials to `config/.env` and run:

```bash
./start.sh
```

Then open:
```
http://localhost:8000/static/index.html
```

**Happy uploading!** 🚀

---

**Need help?** Check the documentation files or run `./verify.sh` to diagnose issues.

**Last Updated**: November 22, 2025
**Status**: ✅ Production Ready
