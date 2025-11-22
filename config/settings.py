import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with sensible defaults."""
    
    # App settings
    app_name: str = "Upload App"
    app_version: str = "1.0.0"
    debug: bool = True  # True for local development
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: str = "sqlite:///./uploads/app.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Upload settings
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    upload_directory: str = "./uploads"
    
    # Azure Storage settings (optional for local development)
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_storage_container_name: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "uploads")
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Chunk settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 52428800))  # 50MB
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 1099511627776))  # 1TB

    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_directory, exist_ok=True)


_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
