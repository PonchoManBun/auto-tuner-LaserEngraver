"""FastAPI server for microscope capture service."""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import (
    CaptureRequest,
    CaptureResponse,
    HealthResponse,
    CameraTestResponse,
)
from .microscope_controller import microscope

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Track busy state
_is_busy = False

# Lazy load Drive and Sheets integrations
_drive_uploader = None
_sheets_logger = None


def get_drive_uploader():
    global _drive_uploader
    if _drive_uploader is None and settings.upload_to_drive:
        from .drive_uploader import drive_uploader
        _drive_uploader = drive_uploader
    return _drive_uploader


def get_sheets_logger():
    global _sheets_logger
    if _sheets_logger is None and settings.log_to_sheets:
        from .sheets_logger import sheets_logger
        _sheets_logger = sheets_logger
    return _sheets_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Microscope Runner service...")
    logger.info(f"Port: {settings.server_port}")
    logger.info(f"Camera index: {settings.camera_index}")
    logger.info(f"Local storage: {settings.local_storage_path}")
    logger.info(f"Upload to Drive: {settings.upload_to_drive}")
    logger.info(f"Log to Sheets: {settings.log_to_sheets}")
    
    # Test camera
    success, error = microscope.test_camera()
    if success:
        logger.info("Microscope camera is available")
    else:
        logger.warning(f"Microscope camera test failed: {error}")
    
    # Test Drive connection
    if settings.upload_to_drive:
        uploader = get_drive_uploader()
        if uploader:
            success, error = uploader.test_connection()
            if success:
                logger.info("Google Drive connected")
            else:
                logger.warning(f"Google Drive connection failed: {error}")
    
    # Test Sheets connection
    if settings.log_to_sheets:
        sheets = get_sheets_logger()
        if sheets:
            success, error = sheets.test_connection()
            if success:
                logger.info("Google Sheets connected")
            else:
                logger.warning(f"Google Sheets connection failed: {error}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Microscope Runner service...")


app = FastAPI(
    title="Microscope Runner",
    description="WA5202 microscope capture service for laser engraving quality analysis",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check service health and camera availability."""
    success, _ = microscope.test_camera()
    
    return HealthResponse(
        status="healthy" if success else "degraded",
        port=settings.server_port,
        camera_available=success,
        camera_index=settings.camera_index,
        is_busy=_is_busy
    )


@app.get("/api/camera/test", response_model=CameraTestResponse)
async def test_camera():
    """Test camera by capturing a test image."""
    global _is_busy
    
    if _is_busy:
        raise HTTPException(status_code=503, detail="Service is busy with another capture")
    
    _is_busy = True
    try:
        success, local_path, error = microscope.capture_test_image()
        
        if success:
            info = microscope.get_camera_info()
            return CameraTestResponse(
                success=True,
                camera_index=settings.camera_index,
                resolution=(info.get("width"), info.get("height")),
                test_image_path=local_path
            )
        else:
            return CameraTestResponse(
                success=False,
                camera_index=settings.camera_index,
                error=error
            )
    finally:
        _is_busy = False


@app.post("/api/capture", response_model=CaptureResponse)
async def capture_image(request: CaptureRequest):
    """Capture a microscope image for quality analysis.
    
    This endpoint:
    1. Captures image from microscope
    2. Saves locally
    3. Uploads to Google Drive (if enabled)
    4. Logs to Google Sheets (if enabled)
    """
    global _is_busy
    
    if _is_busy:
        raise HTTPException(status_code=503, detail="Service is busy with another capture")
    
    _is_busy = True
    try:
        logger.info(f"Capture request: job={request.job_number}, material={request.material_name}")
        
        # 1. Capture image
        success, local_path, error = microscope.capture_image(
            job_number=request.job_number,
            parameter_set_id=request.parameter_set_id
        )
        
        if not success:
            return CaptureResponse(
                success=False,
                job_number=request.job_number,
                error=error
            )
        
        filename = local_path.split("\\")[-1] if local_path else None
        timestamp = datetime.now().isoformat()
        
        # 2. Upload to Google Drive
        drive_file_id = None
        drive_url = None
        if settings.upload_to_drive:
            uploader = get_drive_uploader()
            if uploader:
                upload_success, drive_file_id, drive_url = uploader.upload_image(local_path, filename)
                if upload_success:
                    logger.info(f"Uploaded to Drive: {drive_file_id}")
                else:
                    logger.warning("Drive upload failed, continuing without Drive")
        
        # 3. Log to Google Sheets
        capture_id = None
        if settings.log_to_sheets:
            sheets = get_sheets_logger()
            if sheets:
                log_success, capture_id = sheets.log_capture(
                    job_number=request.job_number,
                    local_path=local_path,
                    drive_file_id=drive_file_id,
                    drive_url=drive_url,
                    material_name=request.material_name,
                    parameters=request.parameters,
                    tuning_session_id=request.tuning_session_id,
                    iteration=request.iteration,
                    notes=request.notes
                )
                if log_success:
                    logger.info(f"Logged to sheet: {capture_id}")
                else:
                    logger.warning("Sheet logging failed, continuing without logging")
        
        return CaptureResponse(
            success=True,
            job_number=request.job_number,
            capture_id=capture_id,
            local_path=local_path,
            filename=filename,
            drive_file_id=drive_file_id,
            drive_url=drive_url,
            capture_timestamp=timestamp,
            resolution=microscope.resolution
        )
        
    except Exception as e:
        logger.error(f"Capture failed: {e}")
        return CaptureResponse(
            success=False,
            job_number=request.job_number,
            error=str(e)
        )
    finally:
        _is_busy = False


@app.get("/api/camera/info")
async def camera_info():
    """Get camera information."""
    return microscope.get_camera_info()


@app.get("/api/status")
async def status():
    """Get detailed service status."""
    camera_ok, camera_error = microscope.test_camera()
    
    drive_ok = False
    sheets_ok = False
    
    if settings.upload_to_drive:
        uploader = get_drive_uploader()
        if uploader:
            drive_ok, _ = uploader.test_connection()
    
    if settings.log_to_sheets:
        sheets = get_sheets_logger()
        if sheets:
            sheets_ok, _ = sheets.test_connection()
    
    return {
        "service": "Microscope Runner",
        "version": "0.2.0",
        "camera": {
            "available": camera_ok,
            "index": settings.camera_index,
            "error": camera_error
        },
        "drive": {
            "enabled": settings.upload_to_drive,
            "connected": drive_ok,
            "folder_id": settings.drive_captures_folder_id if settings.upload_to_drive else None
        },
        "sheets": {
            "enabled": settings.log_to_sheets,
            "connected": sheets_ok,
            "spreadsheet_id": settings.sheets_spreadsheet_id if settings.log_to_sheets else None
        },
        "is_busy": _is_busy
    }
