"""Image quality metrics for microscope captures."""

import cv2
import numpy as np
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def compute_metrics(image_path: str) -> Dict[str, Optional[float]]:
    """
    Compute quality metrics for a microscope image.
    
    Args:
        image_path: Path to the captured image
        
    Returns:
        Dict with metric names and values (0-1 normalized)
    """
    metrics = {
        'metric_contrast': None,
        'metric_sharpness': None,
        'metric_histogram_spread': None,
        'metric_composite': None
    }
    
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not load image: {image_path}")
            return metrics
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Contrast (standard deviation of pixel values, normalized)
        # Higher std = more contrast
        contrast = gray.std() / 128.0  # Normalize to ~0-1 range
        contrast = min(1.0, contrast)  # Cap at 1.0
        metrics['metric_contrast'] = round(contrast, 4)
        
        # 2. Sharpness (Laplacian variance)
        # Higher variance = sharper edges
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        # Normalize (typical range 0-5000 for microscope images)
        sharpness_norm = min(1.0, sharpness / 5000.0)
        metrics['metric_sharpness'] = round(sharpness_norm, 4)
        
        # 3. Histogram spread (how much of the dynamic range is used)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        # Find the range that contains 95% of pixels
        cumsum = np.cumsum(hist)
        total = cumsum[-1]
        low_idx = np.searchsorted(cumsum, total * 0.025)
        high_idx = np.searchsorted(cumsum, total * 0.975)
        spread = (high_idx - low_idx) / 255.0
        metrics['metric_histogram_spread'] = round(spread, 4)
        
        # 4. Composite score (weighted average)
        # Weights: contrast 30%, sharpness 50%, histogram 20%
        composite = (
            0.30 * metrics['metric_contrast'] +
            0.50 * metrics['metric_sharpness'] +
            0.20 * metrics['metric_histogram_spread']
        )
        metrics['metric_composite'] = round(composite, 4)
        
        logger.info(f"Computed metrics: contrast={metrics['metric_contrast']}, "
                   f"sharpness={metrics['metric_sharpness']}, "
                   f"composite={metrics['metric_composite']}")
        
    except Exception as e:
        logger.error(f"Error computing metrics: {e}")
    
    return metrics


def compute_metrics_for_region(image_path: str, 
                                x: int, y: int, 
                                width: int, height: int) -> Dict[str, Optional[float]]:
    """
    Compute metrics for a specific region of the image.
    
    Useful if you want to analyze only the microscope focus area.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return compute_metrics(image_path)  # Fall back to full image
        
        # Crop to region
        h, w = img.shape[:2]
        x = max(0, min(x, w))
        y = max(0, min(y, h))
        x2 = min(x + width, w)
        y2 = min(y + height, h)
        
        cropped = img[y:y2, x:x2]
        
        # Save temp file for analysis
        temp_path = str(Path(image_path).parent / '_temp_crop.jpg')
        cv2.imwrite(temp_path, cropped)
        
        metrics = compute_metrics(temp_path)
        
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error computing region metrics: {e}")
        return compute_metrics(image_path)
