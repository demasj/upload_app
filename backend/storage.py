import json
import os
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UploadMetadata:
    """Represents upload metadata"""
    def __init__(
        self,
        upload_id: str,
        filename: str,
        file_size: int,
        chunk_size: int,
        block_ids: Optional[List[str]] = None,
        completed: bool = False,
        timestamp: Optional[str] = None
    ):
        self.upload_id = upload_id
        self.filename = filename
        self.file_size = file_size
        self.chunk_size = chunk_size
        self.block_ids = block_ids or []
        self.completed = completed
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    @property
    def progress_percentage(self) -> float:
        if self.file_size == 0:
            return 0.0
        bytes_uploaded = len(self.block_ids) * self.chunk_size
        return min(100.0, (bytes_uploaded / self.file_size) * 100)
    
    def to_dict(self):
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "chunk_size": self.chunk_size,
            "block_ids": self.block_ids,
            "progress_percentage": self.progress_percentage,
            "completed": self.completed,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        # Remove computed properties before passing to constructor
        data_copy = data.copy()
        data_copy.pop('progress_percentage', None)
        return cls(**data_copy)


class StorageBackend:
    """Base storage backend interface"""
    
    async def save_metadata(self, metadata: UploadMetadata) -> None:
        raise NotImplementedError
    
    async def get_metadata(self, upload_id: str) -> Optional[UploadMetadata]:
        raise NotImplementedError
    
    async def delete_metadata(self, upload_id: str) -> None:
        raise NotImplementedError
    
    async def add_block_id(self, upload_id: str, block_id: str) -> None:
        raise NotImplementedError
    
    async def get_block_ids(self, upload_id: str) -> List[str]:
        raise NotImplementedError
    
    async def mark_completed(self, upload_id: str) -> None:
        raise NotImplementedError


class RedisStorage(StorageBackend):
    """Redis-based storage backend"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def save_metadata(self, metadata: UploadMetadata) -> None:
        key = f"upload:{metadata.upload_id}"
        await self.redis.set(key, json.dumps(metadata.to_dict()))
    
    async def get_metadata(self, upload_id: str) -> Optional[UploadMetadata]:
        key = f"upload:{upload_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return UploadMetadata.from_dict(json.loads(data))
    
    async def delete_metadata(self, upload_id: str) -> None:
        key = f"upload:{upload_id}"
        await self.redis.delete(key)
    
    async def add_block_id(self, upload_id: str, block_id: str) -> None:
        metadata = await self.get_metadata(upload_id)
        if metadata and block_id not in metadata.block_ids:
            metadata.block_ids.append(block_id)
            await self.save_metadata(metadata)
    
    async def get_block_ids(self, upload_id: str) -> List[str]:
        metadata = await self.get_metadata(upload_id)
        return metadata.block_ids if metadata else []
    
    async def mark_completed(self, upload_id: str) -> None:
        metadata = await self.get_metadata(upload_id)
        if metadata:
            metadata.completed = True
            await self.save_metadata(metadata)


class FileStorage(StorageBackend):
    """File-based storage backend (development only)"""
    
    def __init__(self, storage_dir: str = ".uploads_state"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_file_path(self, upload_id: str) -> str:
        return os.path.join(self.storage_dir, f"{upload_id}.json")
    
    async def save_metadata(self, metadata: UploadMetadata) -> None:
        file_path = self._get_file_path(metadata.upload_id)
        with open(file_path, 'w') as f:
            json.dump(metadata.to_dict(), f)
    
    async def get_metadata(self, upload_id: str) -> Optional[UploadMetadata]:
        file_path = self._get_file_path(upload_id)
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
        return UploadMetadata.from_dict(data)
    
    async def delete_metadata(self, upload_id: str) -> None:
        file_path = self._get_file_path(upload_id)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    async def add_block_id(self, upload_id: str, block_id: str) -> None:
        metadata = await self.get_metadata(upload_id)
        if metadata and block_id not in metadata.block_ids:
            metadata.block_ids.append(block_id)
            await self.save_metadata(metadata)
    
    async def get_block_ids(self, upload_id: str) -> List[str]:
        metadata = await self.get_metadata(upload_id)
        return metadata.block_ids if metadata else []
    
    async def mark_completed(self, upload_id: str) -> None:
        metadata = await self.get_metadata(upload_id)
        if metadata:
            metadata.completed = True
            await self.save_metadata(metadata)
