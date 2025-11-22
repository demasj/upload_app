from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Azure
    azure_storage_account_name: str = ""
    azure_storage_account_key: str = ""
    azure_storage_container_name: str = "uploads"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Upload
    chunk_size: int = 52428800  # 50MB
    max_file_size: int = 1099511627776  # 1TB
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    class Config:
        env_file = "../config/.env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
