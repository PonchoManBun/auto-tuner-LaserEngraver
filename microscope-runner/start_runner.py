#!/usr/bin/env python3
"""Entry point for Microscope Runner service."""

import logging
import uvicorn
from src.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the Microscope Runner service."""
    logger.info("=" * 60)
    logger.info("MICROSCOPE RUNNER - Starting...")
    logger.info("=" * 60)
    logger.info(f"Port: {settings.server_port}")
    logger.info(f"Camera Index: {settings.camera_index}")
    logger.info(f"Local Storage: {settings.local_storage_path}")
    logger.info("=" * 60)
    
    uvicorn.run(
        "src.api_server:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=False
    )


if __name__ == "__main__":
    main()
