"""Microscope capture controller using OpenCV."""

import cv2
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


class MicroscopeController:
    """Controls the WA5202 USB microscope for image capture."""
    
    def __init__(self):
        self.camera_index = settings.camera_index
        self.resolution = (
            settings.camera_resolution_width,
            settings.camera_resolution_height
        )
        self.capture_format = settings.capture_format
        self.capture_quality = settings.capture_quality
        self.storage_path = settings.local_storage_path
        self._camera: Optional[cv2.VideoCapture] = None
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
    
    def test_camera(self) -> Tuple[bool, Optional[str]]:
        """Test if the microscope camera is available."""
        try:
            camera = cv2.VideoCapture(self.camera_index)
            if not camera.isOpened():
                return False, f"Cannot open camera at index {self.camera_index}"
            
            # Try to read a frame
            ret, frame = camera.read()
            camera.release()
            
            if not ret or frame is None:
                return False, "Camera opened but failed to capture frame"
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def capture_image(
        self,
        job_number: str,
        parameter_set_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Capture an image from the microscope.
        
        Returns:
            Tuple of (success, local_path, error_message)
        """
        try:
            # Open camera (auto backend)
            camera = cv2.VideoCapture(self.camera_index)
            
            if not camera.isOpened():
                return False, None, f"Cannot open camera at index {self.camera_index}"
            
            # Set resolution
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            # Warm-up frames (let camera adjust exposure)
            logger.info("Warming up camera...")
            for _ in range(10):
                camera.read()
            
            # Capture frame
            ret, frame = camera.read()
            camera.release()
            
            if not ret or frame is None:
                return False, None, "Failed to capture frame"
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if parameter_set_id:
                filename = f"micro_{job_number}_{parameter_set_id}_{timestamp}.{self.capture_format}"
            else:
                filename = f"micro_{job_number}_{timestamp}.{self.capture_format}"
            
            local_path = os.path.join(self.storage_path, filename)
            
            # Save image
            if self.capture_format.lower() in ['jpg', 'jpeg']:
                cv2.imwrite(local_path, frame, [cv2.IMWRITE_JPEG_QUALITY, self.capture_quality])
            else:
                cv2.imwrite(local_path, frame)
            
            logger.info(f"Captured image: {local_path}")
            return True, local_path, None
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return False, None, str(e)
    
    def capture_test_image(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Capture a test image to verify camera is working."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.capture_image(f"test_{timestamp}")
    
    def get_camera_info(self) -> dict:
        """Get information about the camera."""
        try:
            camera = cv2.VideoCapture(self.camera_index)
            if not camera.isOpened():
                return {"available": False, "error": "Cannot open camera"}
            
            info = {
                "available": True,
                "index": self.camera_index,
                "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": camera.get(cv2.CAP_PROP_FPS),
            }
            camera.release()
            return info
        except Exception as e:
            return {"available": False, "error": str(e)}


# Global instance
microscope = MicroscopeController()
