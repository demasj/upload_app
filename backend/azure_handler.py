import logging
from typing import List
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from datetime import datetime, timedelta
import asyncio

from config import Settings

logger = logging.getLogger(__name__)


class AzureBlobHandler:
    """Handles Azure Blob Storage operations"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.account_name = settings.azure_storage_account_name
        self.account_key = settings.azure_storage_account_key
        self.container_name = settings.azure_storage_container_name
        
        # Use connection string if available, otherwise build from account name/key
        if settings.azure_storage_connection_string:
            connection_string = settings.azure_storage_connection_string
            logger.info("Using Azure Storage connection string (Azurite emulator)")
            # Log the container name only, not the full connection string
            logger.info(f"Container name: {self.container_name}")
        else:
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key};"
                f"EndpointSuffix=core.windows.net"
            )
            logger.info(f"Using Azure Storage account: {self.account_name}")
            logger.info(f"Container name: {self.container_name}")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            logger.info("✓ Azure Blob Storage client initialized successfully")
            
            # Ensure container exists (create if it doesn't)
            self._ensure_container_exists()
        except Exception as e:
            logger.error(f"✗ Failed to initialize Azure Blob Storage client: {str(e)}")
            raise
    
    def _ensure_container_exists(self) -> None:
        """Create container if it doesn't exist"""
        try:
            # Check if container exists
            self.container_client.get_container_properties()
            logger.info(f"✓ Container '{self.container_name}' already exists")
        except Exception as e:
            # Container doesn't exist, try to create it
            if "ContainerNotFound" in str(e) or "ResourceNotFound" in str(e):
                try:
                    self.container_client.create_container()
                    logger.info(f"✓ Created container '{self.container_name}'")
                except Exception as create_error:
                    logger.warning(f"Could not create container '{self.container_name}': {str(create_error)}")
                    # Don't raise - container might already exist or permissions might prevent it
            else:
                logger.warning(f"Could not verify container '{self.container_name}': {str(e)}")
    
    async def stage_block(self, blob_name: str, block_id: str, chunk_data: bytes) -> None:
        """Stage a block for the blob with retry logic"""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                # Run blocking operation in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, blob_client.stage_block, block_id, chunk_data)
                logger.info(f"Staged block {block_id} for blob {blob_name}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for block {block_id}: {str(e)}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Error staging block {block_id}: {str(e)}")
                    raise
    
    async def commit_block_list(self, blob_name: str, block_ids: List[str]) -> None:
        """Commit all staged blocks to finalize the blob with retry logic"""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                # Run blocking operation in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, blob_client.commit_block_list, block_ids)
                logger.info(f"Committed {len(block_ids)} blocks for blob {blob_name}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to commit blocks for {blob_name}: {str(e)}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Error committing block list for {blob_name}: {str(e)}")
                    raise
    
    def generate_sas_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """Generate a SAS URL for the blob"""
        try:
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(add=True, create=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            sas_url = (
                f"https://{self.account_name}.blob.core.windows.net/"
                f"{self.container_name}/{blob_name}?{sas_token}"
            )
            return sas_url
        except Exception as e:
            logger.error(f"Error generating SAS URL for {blob_name}: {str(e)}")
            raise
    
    async def get_blob_properties(self, blob_name: str) -> dict:
        """Get blob properties"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            properties = blob_client.get_blob_properties()
            return {
                "size": properties.size,
                "created": properties.creation_time.isoformat() if properties.creation_time else None,
                "modified": properties.last_modified.isoformat() if properties.last_modified else None
            }
        except Exception as e:
            logger.error(f"Error getting blob properties for {blob_name}: {str(e)}")
            raise
    
    async def delete_blob(self, blob_name: str) -> None:
        """Delete a blob"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Deleted blob {blob_name}")
        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {str(e)}")
            raise
