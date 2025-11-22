#!/usr/bin/env python3
"""List and download files from Azurite storage."""

import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def list_files():
    """List all uploaded files in Azurite."""
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'uploads')
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not set in .env.local")
        sys.exit(1)
    
    try:
        # Connect to Azurite
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        print(f"\n📁 Files in '{container_name}' container:\n")
        
        blobs = container_client.list_blobs()
        file_count = 0
        total_size = 0
        
        for blob in blobs:
            file_count += 1
            size_mb = blob.size / (1024 * 1024)
            total_size += blob.size
            print(f"  📄 {blob.name}")
            print(f"     Size: {size_mb:.2f} MB")
            print(f"     Created: {blob.creation_time}")
            print()
        
        if file_count == 0:
            print("  (No files uploaded yet)")
        else:
            total_mb = total_size / (1024 * 1024)
            print(f"Total: {file_count} file(s), {total_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def download_file(filename, output_path=None):
    """Download a file from Azurite."""
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'uploads')
    
    if not output_path:
        output_path = filename
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=filename
        )
        
        print(f"\n⬇️  Downloading '{filename}'...")
        
        with open(output_path, 'wb') as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())
        
        print(f"✅ Downloaded to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'download':
        if len(sys.argv) < 3:
            print("Usage: python list_azurite_files.py download <filename> [output_path]")
            sys.exit(1)
        download_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        list_files()