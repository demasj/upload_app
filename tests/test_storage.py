import pytest
import json
import tempfile
from unittest.mock import AsyncMock
from backend.storage import UploadMetadata, FileStorage, RedisStorage


class TestUploadMetadata:
    """Test UploadMetadata class"""

    def test_init(self):
        """Test UploadMetadata initialization"""
        metadata = UploadMetadata(
            upload_id="test_id",
            filename="test.txt",
            file_size=100,
            chunk_size=50
        )

        assert metadata.upload_id == "test_id"
        assert metadata.filename == "test.txt"
        assert metadata.file_size == 100
        assert metadata.chunk_size == 50
        assert metadata.block_ids == []
        assert metadata.completed is False
        assert metadata.timestamp is not None

    def test_init_with_params(self):
        """Test UploadMetadata with all parameters"""
        block_ids = ["block1", "block2"]
        metadata = UploadMetadata(
            upload_id="test_id",
            filename="test.txt",
            file_size=100,
            chunk_size=50,
            block_ids=block_ids,
            completed=True,
            timestamp="2023-01-01T00:00:00"
        )

        assert metadata.block_ids == block_ids
        assert metadata.completed is True
        assert metadata.timestamp == "2023-01-01T00:00:00"

    def test_progress_percentage_zero_file_size(self):
        """Test progress percentage with zero file size"""
        metadata = UploadMetadata("id", "file", 0, 50)
        assert metadata.progress_percentage == 0.0

    def test_progress_percentage_partial(self):
        """Test progress percentage with partial upload"""
        metadata = UploadMetadata("id", "file", 100, 50, block_ids=["block1"])
        assert metadata.progress_percentage == 50.0

    def test_progress_percentage_complete(self):
        """Test progress percentage with complete upload"""
        metadata = UploadMetadata("id", "file", 100, 50, block_ids=["block1", "block2"])
        assert metadata.progress_percentage == 100.0

    def test_progress_percentage_over(self):
        """Test progress percentage when blocks exceed file size"""
        metadata = UploadMetadata("id", "file", 75, 50, block_ids=["b1", "b2", "b3"])
        # 3 * 50 = 150 > 75, but min(100.0, (150/75)*100) = min(100, 200) = 100
        assert metadata.progress_percentage == 100.0

    def test_to_dict(self):
        """Test to_dict method"""
        metadata = UploadMetadata("id", "file", 100, 50, ["b1"], True, "ts")
        data = metadata.to_dict()

        expected = {
            "upload_id": "id",
            "filename": "file",
            "file_size": 100,
            "chunk_size": 50,
            "block_ids": ["b1"],
            "progress_percentage": 50.0,
            "completed": True,
            "timestamp": "ts"
        }
        assert data == expected

    def test_from_dict(self):
        """Test from_dict method"""
        data = {
            "upload_id": "id",
            "filename": "file",
            "file_size": 100,
            "chunk_size": 50,
            "block_ids": ["b1"],
            "progress_percentage": 50.0,  # This should be ignored
            "completed": True,
            "timestamp": "ts"
        }
        metadata = UploadMetadata.from_dict(data)

        assert metadata.upload_id == "id"
        assert metadata.filename == "file"
        assert metadata.file_size == 100
        assert metadata.chunk_size == 50
        assert metadata.block_ids == ["b1"]
        assert metadata.completed is True
        assert metadata.timestamp == "ts"


class TestFileStorage:
    """Test FileStorage backend"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_dir):
        """Create FileStorage instance"""
        return FileStorage(storage_dir=temp_dir)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata"""
        return UploadMetadata("test_id", "test.txt", 100, 50, ["b1"], False, "ts")

    @pytest.mark.asyncio
    async def test_save_and_get_metadata(self, storage, sample_metadata):
        """Test saving and retrieving metadata"""
        await storage.save_metadata(sample_metadata)

        retrieved = await storage.get_metadata("test_id")
        assert retrieved is not None
        assert retrieved.upload_id == "test_id"
        assert retrieved.filename == "test.txt"
        assert retrieved.file_size == 100
        assert retrieved.chunk_size == 50
        assert retrieved.block_ids == ["b1"]
        assert retrieved.completed is False

    @pytest.mark.asyncio
    async def test_get_nonexistent_metadata(self, storage):
        """Test getting nonexistent metadata"""
        result = await storage.get_metadata("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_metadata(self, storage, sample_metadata):
        """Test deleting metadata"""
        await storage.save_metadata(sample_metadata)
        assert await storage.get_metadata("test_id") is not None

        await storage.delete_metadata("test_id")
        assert await storage.get_metadata("test_id") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_metadata(self, storage):
        """Test deleting nonexistent metadata (should not raise)"""
        await storage.delete_metadata("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_add_block_id(self, storage, sample_metadata):
        """Test adding block ID"""
        await storage.save_metadata(sample_metadata)
        await storage.add_block_id("test_id", "b2")

        retrieved = await storage.get_metadata("test_id")
        assert retrieved.block_ids == ["b1", "b2"]

    @pytest.mark.asyncio
    async def test_add_duplicate_block_id(self, storage, sample_metadata):
        """Test adding duplicate block ID"""
        await storage.save_metadata(sample_metadata)
        await storage.add_block_id("test_id", "b1")  # Already exists

        retrieved = await storage.get_metadata("test_id")
        assert retrieved.block_ids == ["b1"]  # Should not duplicate

    @pytest.mark.asyncio
    async def test_get_block_ids(self, storage, sample_metadata):
        """Test getting block IDs"""
        await storage.save_metadata(sample_metadata)

        block_ids = await storage.get_block_ids("test_id")
        assert block_ids == ["b1"]

    @pytest.mark.asyncio
    async def test_get_block_ids_nonexistent(self, storage):
        """Test getting block IDs for nonexistent upload"""
        block_ids = await storage.get_block_ids("nonexistent")
        assert block_ids == []

    @pytest.mark.asyncio
    async def test_mark_completed(self, storage, sample_metadata):
        """Test marking upload as completed"""
        await storage.save_metadata(sample_metadata)
        assert (await storage.get_metadata("test_id")).completed is False

        await storage.mark_completed("test_id")

        retrieved = await storage.get_metadata("test_id")
        assert retrieved.completed is True


class TestRedisStorage:
    """Test RedisStorage backend"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis = AsyncMock()
        return redis

    @pytest.fixture
    def storage(self, mock_redis):
        """Create RedisStorage instance"""
        return RedisStorage(mock_redis)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata"""
        return UploadMetadata("test_id", "test.txt", 100, 50, ["b1"], False, "ts")

    @pytest.mark.asyncio
    async def test_save_metadata(self, storage, mock_redis, sample_metadata):
        """Test saving metadata"""
        await storage.save_metadata(sample_metadata)

        mock_redis.set.assert_called_once_with(
            "upload:test_id",
            json.dumps(sample_metadata.to_dict())
        )

    @pytest.mark.asyncio
    async def test_get_metadata(self, storage, mock_redis, sample_metadata):
        """Test getting metadata"""
        mock_redis.get.return_value = json.dumps(sample_metadata.to_dict())

        result = await storage.get_metadata("test_id")

        assert result is not None
        assert result.upload_id == "test_id"
        mock_redis.get.assert_called_once_with("upload:test_id")

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, storage, mock_redis):
        """Test getting nonexistent metadata"""
        mock_redis.get.return_value = None

        result = await storage.get_metadata("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_metadata(self, storage, mock_redis):
        """Test deleting metadata"""
        await storage.delete_metadata("test_id")

        mock_redis.delete.assert_called_once_with("upload:test_id")

    @pytest.mark.asyncio
    async def test_add_block_id(self, storage, mock_redis, sample_metadata):
        """Test adding block ID"""
        # Mock existing metadata
        mock_redis.get.return_value = json.dumps(sample_metadata.to_dict())
        mock_redis.set.return_value = None

        await storage.add_block_id("test_id", "b2")

        # Should get existing, modify, and save
        assert mock_redis.get.call_count >= 1
        assert mock_redis.set.call_count >= 1

    @pytest.mark.asyncio
    async def test_add_block_id_no_metadata(self, storage, mock_redis):
        """Test adding block ID when no metadata exists"""
        mock_redis.get.return_value = None

        await storage.add_block_id("test_id", "b1")

        # Should not call set since no metadata to update
        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_block_ids(self, storage, mock_redis, sample_metadata):
        """Test getting block IDs"""
        mock_redis.get.return_value = json.dumps(sample_metadata.to_dict())

        result = await storage.get_block_ids("test_id")
        assert result == ["b1"]

    @pytest.mark.asyncio
    async def test_get_block_ids_no_metadata(self, storage, mock_redis):
        """Test getting block IDs when no metadata exists"""
        mock_redis.get.return_value = None

        result = await storage.get_block_ids("test_id")
        assert result == []

    @pytest.mark.asyncio
    async def test_mark_completed(self, storage, mock_redis, sample_metadata):
        """Test marking as completed"""
        mock_redis.get.return_value = json.dumps(sample_metadata.to_dict())
        mock_redis.set.return_value = None

        await storage.mark_completed("test_id")

        # Should update and save
        assert mock_redis.get.call_count >= 1
        assert mock_redis.set.call_count >= 1