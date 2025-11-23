import pytest
from config.settings import Settings, get_settings


class TestSettings:
    """Test Settings class"""

    def test_default_settings(self):
        """Test default settings values"""
        settings = Settings()

        assert settings.app_name == "Upload App"
        assert settings.app_version == "1.0.0"
        assert settings.debug is False  # From .env
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.database_url == "sqlite:///./test.db"  # From .env
        assert settings.secret_key == "test-secret-key-change-in-production"  # From .env
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.max_upload_size == 100 * 1024 * 1024  # 100MB
        assert settings.upload_directory == "./uploads"  # From .env
        assert settings.azure_storage_account_name == ""
        assert settings.azure_storage_account_key == ""
        assert settings.azure_storage_container_name == "uploads"
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.chunk_size == 52428800  # 50MB
        assert settings.max_file_size == 1099511627776  # 1TB

    def test_env_file_loading(self):
        """Test that env file is loaded"""
        settings = Settings()
        # The Config class sets env_file = ".env"
        assert settings.Config.env_file == ".env"

    def test_case_insensitive(self):
        """Test case insensitive settings"""
        settings = Settings()
        assert settings.Config.case_sensitive is False

    def test_upload_directory_creation(self, tmp_path, monkeypatch):
        """Test that upload directory is created"""
        custom_dir = tmp_path / "custom_uploads"
        monkeypatch.setenv("UPLOAD_DIRECTORY", str(custom_dir))

        settings = Settings()
        assert custom_dir.exists()

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_env_var_overrides(self, monkeypatch):
        """Test environment variable overrides"""
        monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "test_conn_string")
        monkeypatch.setenv("AZURE_STORAGE_CONTAINER_NAME", "test_container")
        monkeypatch.setenv("REDIS_HOST", "test_redis")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("CHUNK_SIZE", "1048576")
        monkeypatch.setenv("MAX_FILE_SIZE", "2147483648")

        settings = Settings()

        assert settings.azure_storage_connection_string == "test_conn_string"
        assert settings.azure_storage_container_name == "test_container"
        assert settings.redis_host == "test_redis"
        assert settings.redis_port == 6380
        assert settings.chunk_size == 1048576
        assert settings.max_file_size == 2147483648