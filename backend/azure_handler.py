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
        else:
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key};"
                f"EndpointSuffix=core.windows.net"
            )
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
    
    async def stage_block(self, blob_name: str, block_id: str, chunk_data: bytes) -> None:
        """Stage a block for the blob"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            # Run blocking operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob_client.stage_block, block_id, chunk_data)
            logger.info(f"Staged block {block_id} for blob {blob_name}")
        except Exception as e:
            logger.error(f"Error staging block {block_id}: {str(e)}")
            raise
    
    async def commit_block_list(self, blob_name: str, block_ids: List[str]) -> None:
        """Commit all staged blocks to finalize the blob"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            # Run blocking operation in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob_client.commit_block_list, block_ids)
            logger.info(f"Committed {len(block_ids)} blocks for blob {blob_name}")
        except Exception as e:
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
