"""Pydantic models for API requests and responses."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CaptureRequest(BaseModel):
    """Request to capture a microscope image."""
    job_number: str
    parameter_set_id: Optional[str] = None
    material_name: Optional[str] = None
    parameters: Optional[dict] = None  # Laser parameters for logging
    tuning_session_id: Optional[str] = None
    iteration: Optional[int] = None
    notes: Optional[str] = None


class CaptureResponse(BaseModel):
    """Response after capturing an image."""
    success: bool
    job_number: str
    capture_id: Optional[str] = None
    local_path: Optional[str] = None
    filename: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_url: Optional[str] = None
    capture_timestamp: Optional[str] = None
    resolution: Optional[tuple] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str = "Microscope Runner"
    port: int
    camera_available: bool
    camera_index: int
    is_busy: bool = False


class CameraTestResponse(BaseModel):
    """Camera test response."""
    success: bool
    camera_index: int
    resolution: Optional[tuple] = None
    test_image_path: Optional[str] = None
    error: Optional[str] = None
