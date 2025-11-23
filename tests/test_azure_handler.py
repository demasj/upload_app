import pytest
from unittest.mock import MagicMock, patch
from backend.azure_handler import AzureBlobHandler
from config.settings import Settings


class TestAzureBlobHandler:
    """Test AzureBlobHandler class"""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings"""
        settings = MagicMock(spec=Settings)
        settings.azure_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net"
        settings.azure_storage_account_name = "testaccount"
        settings.azure_storage_account_key = "testkey"
        settings.azure_storage_container_name = "testcontainer"
        return settings

    @pytest.fixture
    def mock_blob_service_client(self):
        """Create mock blob service client"""
        client = MagicMock()
        container_client = MagicMock()
        client.get_container_client.return_value = container_client
        return client

    @pytest.fixture
    def mock_container_client(self, mock_blob_service_client):
        """Create mock container client"""
        return mock_blob_service_client.get_container_client.return_value

    @patch('backend.azure_handler.BlobServiceClient')
    def test_init_with_connection_string(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test initialization with connection string"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client

        handler = AzureBlobHandler(mock_settings)

        mock_bs_client.from_connection_string.assert_called_once_with(mock_settings.azure_storage_connection_string)
        assert handler.blob_service_client == mock_blob_service_client
        assert handler.container_client == mock_blob_service_client.get_container_client.return_value

    @patch('backend.azure_handler.BlobServiceClient')
    def test_init_without_connection_string(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test initialization without connection string"""
        mock_settings.azure_storage_connection_string = ""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client

        expected_conn_string = (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={mock_settings.azure_storage_account_name};"
            f"AccountKey={mock_settings.azure_storage_account_key};"
            f"EndpointSuffix=core.windows.net"
        )

        handler = AzureBlobHandler(mock_settings)

        mock_bs_client.from_connection_string.assert_called_once_with(expected_conn_string)
        assert handler.blob_service_client == mock_blob_service_client

    @patch('backend.azure_handler.BlobServiceClient')
    def test_init_container_exists(self, mock_bs_client, mock_settings, mock_blob_service_client, mock_container_client):
        """Test container exists check"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        mock_container_client.get_container_properties.return_value = None  # Exists

        handler = AzureBlobHandler(mock_settings)

        mock_container_client.get_container_properties.assert_called_once()
        assert handler is not None

    @patch('backend.azure_handler.BlobServiceClient')
    def test_init_container_not_found_create_success(self, mock_bs_client, mock_settings, mock_blob_service_client, mock_container_client):
        """Test container not found and creation succeeds"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        mock_container_client.get_container_properties.side_effect = Exception("ContainerNotFound")
        mock_container_client.create_container.return_value = None

        handler = AzureBlobHandler(mock_settings)

        mock_container_client.create_container.assert_called_once()
        assert handler is not None

    @patch('backend.azure_handler.BlobServiceClient')
    def test_init_container_create_fails(self, mock_bs_client, mock_settings, mock_blob_service_client, mock_container_client):
        """Test container creation fails but doesn't raise"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        mock_container_client.get_container_properties.side_effect = Exception("ContainerNotFound")
        mock_container_client.create_container.side_effect = Exception("Permission denied")

        handler = AzureBlobHandler(mock_settings)  # Should not raise

        mock_container_client.create_container.assert_called_once()
        assert handler is not None

    def test_init_blob_service_client_fails(self, mock_bs_client, mock_settings):
        """Test BlobServiceClient initialization fails"""
        mock_bs_client.from_connection_string.side_effect = Exception("Invalid connection string")

        with pytest.raises(Exception, match="Invalid connection string"):
            AzureBlobHandler(mock_settings)

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_stage_block_success(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test successful block staging"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        # Mock successful staging
        blob_client.stage_block.return_value = None

        await handler.stage_block("test_blob", "block_id", b"chunk_data")

        mock_blob_service_client.get_blob_client.assert_called_once_with(
            container=mock_settings.azure_storage_container_name,
            blob="test_blob"
        )
        blob_client.stage_block.assert_called_once_with("block_id", b"chunk_data")

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_stage_block_retry_success(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test block staging with retry success"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        # Fail twice, succeed on third
        blob_client.stage_block.side_effect = [Exception("Network error"), Exception("Timeout"), None]

        await handler.stage_block("test_blob", "block_id", b"chunk_data")

        assert blob_client.stage_block.call_count == 3

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_stage_block_max_retries_exceeded(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test block staging fails after max retries"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.stage_block.side_effect = Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            await handler.stage_block("test_blob", "block_id", b"chunk_data")

        assert blob_client.stage_block.call_count == 3

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_commit_block_list_success(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test successful block list commit"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.commit_block_list.return_value = None

        await handler.commit_block_list("test_blob", ["block1", "block2"])

        mock_blob_service_client.get_blob_client.assert_called_once_with(
            container=mock_settings.azure_storage_container_name,
            blob="test_blob"
        )
        blob_client.commit_block_list.assert_called_once_with(["block1", "block2"])

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_commit_block_list_retry_success(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test commit block list with retry success"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.commit_block_list.side_effect = [Exception("Network"), Exception("Timeout"), None]

        await handler.commit_block_list("test_blob", ["block1"])

        assert blob_client.commit_block_list.call_count == 3

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_commit_block_list_max_retries_exceeded(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test commit block list fails after max retries"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.commit_block_list.side_effect = Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            await handler.commit_block_list("test_blob", ["block1"])

        assert blob_client.commit_block_list.call_count == 3

    @patch('backend.azure_handler.BlobServiceClient')
    @patch('backend.azure_handler.generate_blob_sas')
    @patch('backend.azure_handler.datetime')
    def test_generate_sas_url(self, mock_datetime, mock_generate_sas, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test SAS URL generation"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        mock_generate_sas.return_value = "sas_token"
        mock_datetime.utcnow.return_value = MagicMock()

        url = handler.generate_sas_url("test_blob", 24)

        expected_url = (
            f"https://{mock_settings.azure_storage_account_name}.blob.core.windows.net/"
            f"{mock_settings.azure_storage_container_name}/test_blob?sas_token"
        )
        assert url == expected_url

        mock_generate_sas.assert_called_once()

    @patch('backend.azure_handler.BlobServiceClient')
    @patch('backend.azure_handler.generate_blob_sas')
    @patch('backend.azure_handler.datetime')
    def test_generate_sas_url_error(self, mock_datetime, mock_generate_sas, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test SAS URL generation error"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        mock_generate_sas.side_effect = Exception("SAS generation failed")

        with pytest.raises(Exception, match="SAS generation failed"):
            handler.generate_sas_url("test_blob", 24)

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_get_blob_properties(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test getting blob properties"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        mock_properties = MagicMock()
        mock_properties.size = 1024
        mock_properties.creation_time = MagicMock()
        mock_properties.creation_time.isoformat.return_value = "2023-01-01T00:00:00"
        mock_properties.last_modified = MagicMock()
        mock_properties.last_modified.isoformat.return_value = "2023-01-02T00:00:00"

        blob_client.get_blob_properties.return_value = mock_properties

        result = await handler.get_blob_properties("test_blob")

        expected = {
            "size": 1024,
            "created": "2023-01-01T00:00:00",
            "modified": "2023-01-02T00:00:00"
        }
        assert result == expected

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_get_blob_properties_error(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test getting blob properties error"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.get_blob_properties.side_effect = Exception("Blob not found")

        with pytest.raises(Exception, match="Blob not found"):
            await handler.get_blob_properties("test_blob")

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_delete_blob(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test blob deletion"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.delete_blob.return_value = None

        await handler.delete_blob("test_blob")

        mock_blob_service_client.get_blob_client.assert_called_once_with(
            container=mock_settings.azure_storage_container_name,
            blob="test_blob"
        )
        blob_client.delete_blob.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.azure_handler.BlobServiceClient')
    async def test_delete_blob_error(self, mock_bs_client, mock_settings, mock_blob_service_client):
        """Test blob deletion error"""
        mock_bs_client.from_connection_string.return_value = mock_blob_service_client
        handler = AzureBlobHandler(mock_settings)

        blob_client = MagicMock()
        mock_blob_service_client.get_blob_client.return_value = blob_client

        blob_client.delete_blob.side_effect = Exception("Delete failed")

        with pytest.raises(Exception, match="Delete failed"):
            await handler.delete_blob("test_blob")