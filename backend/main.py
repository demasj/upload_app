import logging
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from config import get_settings
from .storage import FileStorage, UploadMetadata
from .azure_handler import AzureBlobHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request models
class InitUploadRequest(BaseModel):
    filename: str
    file_size: int


class CompleteUploadRequest(BaseModel):
    upload_id: str

# Initialize settings
settings = get_settings()

# Initialize storage backend (using FileStorage for development, switch to RedisStorage for production)
storage_backend = FileStorage()

# Initialize Azure handler
azure_handler = AzureBlobHandler(settings)

# Initialize FastAPI app
app = FastAPI(title="Large File Upload API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/")
async def root():
    """Serve the frontend"""
    return JSONResponse({"message": "Large File Upload API", "docs": "/docs"})


@app.post("/api/upload/init")
async def init_upload(request: InitUploadRequest):
    """Initialize a new upload"""
    try:
        # Validate file size
        if request.file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed ({settings.max_file_size} bytes)"
            )
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = UploadMetadata(
            upload_id=upload_id,
            filename=request.filename,
            file_size=request.file_size,
            chunk_size=settings.chunk_size
        )
        
        # Save metadata
        await storage_backend.save_metadata(metadata)
        
        logger.info(f"Initialized upload {upload_id} for file {request.filename}")
        
        return JSONResponse({
            "upload_id": upload_id,
            "chunk_size": settings.chunk_size,
            "message": "Upload initialized"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload a single chunk"""
    try:
        # Get metadata
        metadata = await storage_backend.get_metadata(upload_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        if metadata.completed:
            raise HTTPException(status_code=400, detail="Upload already completed")
        
        # Read chunk data
        chunk_data = await file.read()
        
        # Generate block ID (base64 encoded)
        import base64
        block_id = base64.b64encode(f"{upload_id}_{chunk_index}".encode()).decode()
        
        # Stage the block in Azure
        await azure_handler.stage_block(metadata.filename, block_id, chunk_data)
        
        # Add block ID to metadata
        await storage_backend.add_block_id(upload_id, block_id)
        
        # Get updated metadata
        updated_metadata = await storage_backend.get_metadata(upload_id)
        
        logger.info(f"Uploaded chunk {chunk_index} for upload {upload_id}")
        
        return JSONResponse({
            "chunk_index": chunk_index,
            "block_id": block_id,
            "progress_percentage": updated_metadata.progress_percentage,
            "message": "Chunk uploaded successfully"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/complete")
async def complete_upload(request: CompleteUploadRequest, background_tasks: BackgroundTasks):
    """Finalize the upload by committing all blocks"""
    try:
        # Get metadata
        metadata = await storage_backend.get_metadata(request.upload_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        if metadata.completed:
            raise HTTPException(status_code=400, detail="Upload already completed")
        
        # Commit all blocks
        await azure_handler.commit_block_list(metadata.filename, metadata.block_ids)
        
        # Mark as completed
        await storage_backend.mark_completed(request.upload_id)
        
        logger.info(f"Completed upload {request.upload_id}")
        
        return JSONResponse({
            "upload_id": request.upload_id,
            "filename": metadata.filename,
            "file_size": metadata.file_size,
            "blocks_count": len(metadata.block_ids),
            "message": "Upload completed successfully"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/upload/status/{upload_id}")
async def get_upload_status(upload_id: str):
    """Get upload status"""
    try:
        metadata = await storage_backend.get_metadata(upload_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        return JSONResponse(metadata.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/upload/resume/{upload_id}")
async def resume_upload(upload_id: str):
    """Resume a failed upload (returns already uploaded block IDs)"""
    try:
        metadata = await storage_backend.get_metadata(upload_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        return JSONResponse({
            "upload_id": upload_id,
            "filename": metadata.filename,
            "file_size": metadata.file_size,
            "chunk_size": metadata.chunk_size,
            "completed_chunks": len(metadata.block_ids),
            "block_ids": metadata.block_ids,
            "progress_percentage": metadata.progress_percentage,
            "message": "Upload resumed"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/upload/{upload_id}")
async def delete_upload(upload_id: str):
    """Cancel/delete an upload"""
    try:
        metadata = await storage_backend.get_metadata(upload_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Delete metadata
        await storage_backend.delete_metadata(upload_id)
        
        logger.info(f"Deleted upload {upload_id}")
        
        return JSONResponse({
            "upload_id": upload_id,
            "message": "Upload deleted"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """Get client-side configuration"""
    return JSONResponse({
        "chunk_size": settings.chunk_size,
        "max_file_size": settings.max_file_size
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )
