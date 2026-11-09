"""
Application Configuration Module.

Loads and validates environment variables using Pydantic Settings V2.
Supports dual-tier database configuration (SQLite / PostgreSQL) and
configurable AI model endpoints.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application Settings Schema and Environment Loader."""

    # Application Information
    APP_NAME: str = "Multi-Agent AI Business Analyst"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Security & Authentication
    SECRET_KEY: str = "dev-secret-key-multi-agent-bi-system-change-in-production-32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ALLOW_GUEST_MODE: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./data/bi_system.db"

    # AI / LLM Configuration (OpenRouter Free Tier / Local Ollama)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_LLM_MODEL: str = "google/gemini-2.0-flash-exp:free"
    FALLBACK_LLM_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    AI_REQUEST_TIMEOUT_SECONDS: int = 45
    MAX_RETRIES: int = 3

    # Local Ollama Support (Optional Offline Mode)
    USE_LOCAL_OLLAMA: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # File Storage & Limits
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: str = ".csv,.xlsx,.xls"
    TEMP_UPLOAD_DIR: str = "./data/uploads"
    REPORTS_DIR: str = "./data/reports"
    FILE_RETENTION_HOURS: int = 24

    # CORS Settings
    CORS_ORIGINS: Union[str, List[str]] = "*"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string or list to List of origin URLs."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions into a list of lowercase extensions."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Calculate maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def upload_dir_path(self) -> Path:
        """Resolve absolute path to temporary uploads folder."""
        path = BASE_DIR / self.TEMP_UPLOAD_DIR.lstrip("./")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_dir_path(self) -> Path:
        """Resolve absolute path to generated reports folder."""
        path = BASE_DIR / self.REPORTS_DIR.lstrip("./")
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance singleton."""
    return Settings()

