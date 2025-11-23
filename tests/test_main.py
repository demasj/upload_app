import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import io

from backend.main import app
from backend.storage import UploadMetadata


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_globals():
    """Mock global dependencies"""
    with patch('backend.main.storage_backend', new_callable=AsyncMock) as mock_storage, \
         patch('backend.main.azure_handler', new_callable=AsyncMock) as mock_azure, \
         patch('backend.main.settings') as mock_settings:

        # Configure mock settings
        mock_settings.max_file_size = 1099511627776
        mock_settings.chunk_size = 52428800

        yield mock_storage, mock_azure, mock_settings


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return UploadMetadata("test_id", "test.txt", 100, 50, ["block1"], False, "2023-01-01T00:00:00")


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_serves_html(self, client):
        """Test root endpoint serves HTML"""
        with patch('backend.main.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = "<html>Test</html>"
            mock_open.return_value.__enter__.return_value = mock_file

            response = client.get("/")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/html; charset=utf-8"
            assert "<html>Test</html>" in response.text


class TestUploadInit:
    """Test upload initialization endpoint"""

    @patch('backend.main.uuid')
    def test_init_upload_success(self, mock_uuid, mock_globals, client):
        """Test successful upload initialization"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_uuid.uuid4.return_value = MagicMock()
        mock_uuid.uuid4.return_value.__str__ = lambda x: "test-upload-id"

        response = client.post("/api/upload/init", json={
            "filename": "test.txt",
            "file_size": 100
        })

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == "test-upload-id"
        assert data["chunk_size"] == 52428800  # Default chunk size
        assert data["message"] == "Upload initialized"

        mock_storage.save_metadata.assert_called_once()

    def test_init_upload_file_too_large(self, mock_globals, client):
        """Test upload initialization with file too large"""
        mock_storage, mock_azure, mock_settings = mock_globals

        response = client.post("/api/upload/init", json={
            "filename": "test.txt",
            "file_size": 2000000000000  # Larger than max_file_size
        })

        assert response.status_code == 400
        data = response.json()
        assert "exceeds maximum allowed" in data["detail"]

    def test_init_upload_storage_error(self, mock_globals, client):
        """Test upload initialization with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.save_metadata.side_effect = Exception("Storage error")

        response = client.post("/api/upload/init", json={
            "filename": "test.txt",
            "file_size": 100
        })

        assert response.status_code == 500
        data = response.json()
        assert "Storage error" in data["detail"]


class TestUploadChunk:
    """Test chunk upload endpoint"""

    @patch('base64.b64encode')
    def test_upload_chunk_success(self, mock_b64encode, mock_globals, client, sample_metadata):
        """Test successful chunk upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_b64encode.return_value.decode.return_value = "encoded_block_id"

        # Create test file
        test_file = io.BytesIO(b"chunk data")
        files = {"file": ("chunk.txt", test_file, "application/octet-stream")}
        data = {"upload_id": "test_id", "chunk_index": 1}

        response = client.post("/api/upload/chunk", data=data, files=files)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["chunk_index"] == 1
        assert "block_id" in response_data
        assert "progress_percentage" in response_data

        mock_azure.stage_block.assert_called_once()
        mock_storage.add_block_id.assert_called_once_with("test_id", "encoded_block_id")

    def test_upload_chunk_upload_not_found(self, mock_globals, client):
        """Test chunk upload with nonexistent upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = None

        test_file = io.BytesIO(b"chunk data")
        files = {"file": ("chunk.txt", test_file, "application/octet-stream")}
        data = {"upload_id": "nonexistent", "chunk_index": 1}

        response = client.post("/api/upload/chunk", data=data, files=files)

        assert response.status_code == 404
        assert "Upload session not found" in response.json()["detail"]

    def test_upload_chunk_already_completed(self, mock_globals, client, sample_metadata):
        """Test chunk upload for completed upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        completed_metadata = UploadMetadata("id", "file", 100, 50, [], True)
        mock_storage.get_metadata.return_value = completed_metadata

        test_file = io.BytesIO(b"chunk data")
        files = {"file": ("chunk.txt", test_file, "application/octet-stream")}
        data = {"upload_id": "id", "chunk_index": 1}

        response = client.post("/api/upload/chunk", data=data, files=files)

        assert response.status_code == 400
        assert "Upload already completed" in response.json()["detail"]

    def test_upload_chunk_azure_error(self, mock_globals, client, sample_metadata):
        """Test chunk upload with Azure error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_azure.stage_block.side_effect = Exception("Azure error")

        test_file = io.BytesIO(b"chunk data")
        files = {"file": ("chunk.txt", test_file, "application/octet-stream")}
        data = {"upload_id": "test_id", "chunk_index": 1}

        response = client.post("/api/upload/chunk", data=data, files=files)

        assert response.status_code == 500
        assert "Azure error" in response.json()["detail"]

    def test_upload_chunk_storage_error(self, mock_globals, client, sample_metadata):
        """Test chunk upload with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_storage.add_block_id.side_effect = Exception("Storage error")

        test_file = io.BytesIO(b"chunk data")
        files = {"file": ("chunk.txt", test_file, "application/octet-stream")}
        data = {"upload_id": "test_id", "chunk_index": 1}

        response = client.post("/api/upload/chunk", data=data, files=files)

        assert response.status_code == 500
        assert "Storage error" in response.json()["detail"]


class TestCompleteUpload:
    """Test upload completion endpoint"""

    @patch('backend.main.BackgroundTasks')
    def test_complete_upload_success(self, mock_bg_tasks, mock_globals, client, sample_metadata):
        """Test successful upload completion"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata

        response = client.post("/api/upload/complete", json={"upload_id": "test_id"})

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == "test_id"
        assert data["filename"] == "test.txt"
        assert data["file_size"] == 100
        assert data["blocks_count"] == 1
        assert data["message"] == "Upload completed successfully"

        mock_azure.commit_block_list.assert_called_once_with("test.txt", ["block1"])
        mock_storage.mark_completed.assert_called_once_with("test_id")

    def test_complete_upload_not_found(self, mock_globals, client):
        """Test complete upload with nonexistent upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = None

        response = client.post("/api/upload/complete", json={"upload_id": "nonexistent"})

        assert response.status_code == 404
        assert "Upload session not found" in response.json()["detail"]

    def test_complete_upload_already_completed(self, mock_globals, client):
        """Test complete upload for already completed upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        completed_metadata = UploadMetadata("id", "file", 100, 50, [], True)
        mock_storage.get_metadata.return_value = completed_metadata

        response = client.post("/api/upload/complete", json={"upload_id": "id"})

        assert response.status_code == 400
        assert "Upload already completed" in response.json()["detail"]

    def test_complete_upload_azure_error(self, mock_globals, client, sample_metadata):
        """Test complete upload with Azure error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_azure.commit_block_list.side_effect = Exception("Azure error")

        response = client.post("/api/upload/complete", json={"upload_id": "test_id"})

        assert response.status_code == 500
        assert "Azure error" in response.json()["detail"]

    def test_complete_upload_storage_error(self, mock_globals, client, sample_metadata):
        """Test complete upload with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_storage.mark_completed.side_effect = Exception("Storage error")

        response = client.post("/api/upload/complete", json={"upload_id": "test_id"})

        assert response.status_code == 500
        assert "Storage error" in response.json()["detail"]


class TestUploadStatus:
    """Test upload status endpoint"""

    def test_get_upload_status_success(self, mock_globals, client, sample_metadata):
        """Test successful status retrieval"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata

        response = client.get("/api/upload/status/test_id")

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == "test_id"
        assert data["filename"] == "test.txt"
        assert data["progress_percentage"] == 50.0

    def test_get_upload_status_not_found(self, mock_globals, client):
        """Test status retrieval for nonexistent upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = None

        response = client.get("/api/upload/status/nonexistent")

        assert response.status_code == 404
        assert "Upload session not found" in response.json()["detail"]

    def test_get_upload_status_storage_error(self, mock_globals, client):
        """Test status retrieval with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.side_effect = Exception("Storage error")

        response = client.get("/api/upload/status/test_id")

        assert response.status_code == 500
        assert "Storage error" in response.json()["detail"]


class TestResumeUpload:
    """Test upload resume endpoint"""

    def test_resume_upload_success(self, mock_globals, client, sample_metadata):
        """Test successful upload resume"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata

        response = client.get("/api/upload/resume/test_id")

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == "test_id"
        assert data["filename"] == "test.txt"
        assert data["completed_chunks"] == 1
        assert data["block_ids"] == ["block1"]

    def test_resume_upload_not_found(self, mock_globals, client):
        """Test resume for nonexistent upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = None

        response = client.get("/api/upload/resume/nonexistent")

        assert response.status_code == 404
        assert "Upload session not found" in response.json()["detail"]

    def test_resume_upload_storage_error(self, mock_globals, client):
        """Test resume with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.side_effect = Exception("Storage error")

        response = client.get("/api/upload/resume/test_id")

        assert response.status_code == 500
        assert "Storage error" in response.json()["detail"]


class TestDeleteUpload:
    """Test upload deletion endpoint"""

    def test_delete_upload_success(self, mock_globals, client, sample_metadata):
        """Test successful upload deletion"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata

        response = client.delete("/api/upload/test_id")

        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == "test_id"
        assert data["message"] == "Upload deleted"

        mock_storage.delete_metadata.assert_called_once_with("test_id")

    def test_delete_upload_not_found(self, mock_globals, client):
        """Test deletion of nonexistent upload"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = None

        response = client.delete("/api/upload/nonexistent")

        assert response.status_code == 404
        assert "Upload session not found" in response.json()["detail"]

    def test_delete_upload_storage_error(self, mock_globals, client, sample_metadata):
        """Test deletion with storage error"""
        mock_storage, mock_azure, mock_settings = mock_globals
        mock_storage.get_metadata.return_value = sample_metadata
        mock_storage.delete_metadata.side_effect = Exception("Storage error")

        response = client.delete("/api/upload/test_id")

        assert response.status_code == 500
        assert "Storage error" in response.json()["detail"]


class TestConfigEndpoint:
    """Test config endpoint"""

    def test_get_config(self, client):
        """Test config endpoint returns configuration"""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert "chunk_size" in data
        assert "max_file_size" in data
        assert data["chunk_size"] == 52428800
        assert data["max_file_size"] == 1099511627776


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, mock_globals, client):
        """Test health check endpoint"""
        mock_storage, mock_azure, mock_settings = mock_globals
        # Configure mock settings
        mock_settings.app_name = "Test App"
        mock_settings.app_version = "1.0.0"
        mock_settings.host = "0.0.0.0"
        mock_settings.port = 8000
        mock_settings.debug = True
        mock_settings.chunk_size = 52428800
        mock_settings.max_file_size = 1099511627776
        mock_settings.redis_host = "localhost"
        mock_settings.redis_port = 6379
        mock_settings.azure_storage_connection_string = "azurite_conn"
        mock_settings.azure_storage_container_name = "uploads"
        mock_settings.azure_storage_account_name = "testaccount"

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == "Test App"
        assert data["config"]["azure_storage"]["using_azurite_emulator"] is True