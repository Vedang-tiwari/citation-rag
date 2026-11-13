"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Set
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General App Config
    APP_NAME: str = Field(default="Citation RAG", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind server")
    PORT: int = Field(default=8000, description="Port to bind server")

    # Storage Paths
    BASE_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )
    UPLOAD_DIR: Path = Field(default=Path("data/uploads"), description="Directory for raw uploaded files")
    PROCESSED_DIR: Path = Field(
        default=Path("data/processed"), description="Directory for processed chunk metadata"
    )

    # File Upload Limits & Validation
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum allowed upload file size in bytes",
    )
    ALLOWED_EXTENSIONS: Set[str] = Field(
        default={".pdf", ".txt", ".docx"},
        description="Allowed file extensions (lowercase including leading dot)",
    )
    ALLOWED_MIME_TYPES: Set[str] = Field(
        default={
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/octet-stream",  # Often sent for binary/docx by some clients
        },
        description="Allowed MIME types for uploaded files",
    )

    # Chunking Configuration
    DEFAULT_CHUNK_SIZE: int = Field(
        default=500, description="Default chunk size in characters"
    )
    DEFAULT_CHUNK_OVERLAP: int = Field(
        default=100, description="Default chunk overlap in characters"
    )
    MIN_CHUNK_SIZE: int = Field(
        default=50, description="Minimum allowed chunk size"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    def ensure_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        resolved_upload = self.UPLOAD_DIR if self.UPLOAD_DIR.is_absolute() else self.BASE_DIR / self.UPLOAD_DIR
        resolved_processed = (
            self.PROCESSED_DIR if self.PROCESSED_DIR.is_absolute() else self.BASE_DIR / self.PROCESSED_DIR
        )
        resolved_upload.mkdir(parents=True, exist_ok=True)
        resolved_processed.mkdir(parents=True, exist_ok=True)


settings = Settings()

