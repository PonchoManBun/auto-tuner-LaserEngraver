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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Microscope Runner service...")
    logger.info(f"Port: {settings.server_port}")
    logger.info(f"Camera index: {settings.camera_index}")
    logger.info(f"Local storage: {settings.local_storage_path}")
    
    # Test camera
    success, error = microscope.test_camera()
    if success:
        logger.info("Microscope camera is available")
    else:
        logger.warning(f"Microscope camera test failed: {error}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Microscope Runner service...")


app = FastAPI(
    title="Microscope Runner",
    description="WA5202 microscope capture service for laser engraving quality analysis",
    version="0.1.0",
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
    """Capture a microscope image for quality analysis."""
    global _is_busy
    
    if _is_busy:
        raise HTTPException(status_code=503, detail="Service is busy with another capture")
    
    _is_busy = True
    try:
        logger.info(f"Capture request: job={request.job_number}, param_set={request.parameter_set_id}")
        
        success, local_path, error = microscope.capture_image(
            job_number=request.job_number,
            parameter_set_id=request.parameter_set_id
        )
        
        if success:
            filename = local_path.split("\\")[-1] if local_path else None
            return CaptureResponse(
                success=True,
                job_number=request.job_number,
                local_path=local_path,
                filename=filename,
                capture_timestamp=datetime.now().isoformat(),
                resolution=microscope.resolution
            )
        else:
            return CaptureResponse(
                success=False,
                job_number=request.job_number,
                error=error
            )
    finally:
        _is_busy = False


@app.get("/api/camera/info")
async def camera_info():
    """Get camera information."""
    return microscope.get_camera_info()
