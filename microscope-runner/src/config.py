"""Configuration management for Microscope Runner."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    server_port: int = Field(default=8005, alias="SERVER_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Camera
    camera_index: int = Field(default=1, alias="CAMERA_INDEX")
    camera_resolution_width: int = Field(default=1920, alias="CAMERA_RESOLUTION_WIDTH")
    camera_resolution_height: int = Field(default=1080, alias="CAMERA_RESOLUTION_HEIGHT")
    capture_format: str = Field(default="jpg", alias="CAPTURE_FORMAT")
    capture_quality: int = Field(default=95, alias="CAPTURE_QUALITY")
    
    # Storage
    local_storage_path: str = Field(
        default=r"F:\dev\auto-tuner-LaserEngraver\microscope-runner\captures",
        alias="LOCAL_STORAGE_PATH"
    )
    filename_pattern: str = Field(
        default="micro_{job_number}_{timestamp}.jpg",
        alias="FILENAME_PATTERN"
    )
    
    # Timeouts
    camera_timeout_seconds: int = Field(default=10, alias="CAMERA_TIMEOUT_SECONDS")
    
    # Google Drive settings
    drive_credentials_path: str = Field(
        default=r"C:\Users\ctsul\.openclaw\googlechat-service-account.json",
        alias="DRIVE_CREDENTIALS_PATH"
    )
    drive_captures_folder_id: str = Field(
        default="12CSt2Zj47DFrXSy4BglLg6QBiV1FcHxz",
        alias="DRIVE_CAPTURES_FOLDER_ID"
    )
    
    # Google Sheets settings
    sheets_spreadsheet_id: str = Field(
        default="1aAIVfx6EfBmH8g3Zny5JXch079g3IM9fogNtzLH1tJk",
        alias="SHEETS_SPREADSHEET_ID"
    )
    
    # Feature flags
    upload_to_drive: bool = Field(default=True, alias="UPLOAD_TO_DRIVE")
    log_to_sheets: bool = Field(default=True, alias="LOG_TO_SHEETS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
