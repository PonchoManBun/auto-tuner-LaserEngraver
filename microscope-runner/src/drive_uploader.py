"""Google Drive upload functionality for microscope captures."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .config import settings

logger = logging.getLogger(__name__)


class DriveUploader:
    """Handles uploading microscope images to Google Drive."""
    
    def __init__(self):
        self.credentials_path = settings.drive_credentials_path
        self.captures_folder_id = settings.drive_captures_folder_id
        self._service = None
    
    def _get_service(self):
        """Get or create the Drive service."""
        if self._service is None:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self._service = build('drive', 'v3', credentials=creds)
        return self._service
    
    def _get_or_create_month_folder(self) -> str:
        """Get or create the current month's subfolder."""
        service = self._get_service()
        month_name = datetime.now().strftime('%Y-%m')
        
        # Check if month folder exists
        query = f"name='{month_name}' and '{self.captures_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields='files(id)').execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create month folder
        metadata = {
            'name': month_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.captures_folder_id]
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        logger.info(f"Created month folder: {month_name}")
        return folder['id']
    
    def upload_image(self, local_path: str, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload an image to Google Drive.
        
        Returns:
            Tuple of (success, file_id, web_view_link)
        """
        try:
            service = self._get_service()
            
            # Get the month folder
            parent_folder_id = self._get_or_create_month_folder()
            
            # Upload file
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            
            media = MediaFileUpload(
                local_path,
                mimetype='image/jpeg',
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            web_link = file.get('webViewLink')
            
            logger.info(f"Uploaded to Drive: {filename} (ID: {file_id})")
            return True, file_id, web_link
            
        except Exception as e:
            logger.error(f"Drive upload failed: {e}")
            return False, None, None
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to Google Drive."""
        try:
            service = self._get_service()
            # Try to get info about the captures folder
            folder = service.files().get(
                fileId=self.captures_folder_id,
                fields='id, name'
            ).execute()
            logger.info(f"Connected to Drive folder: {folder.get('name')}")
            return True, None
        except Exception as e:
            logger.error(f"Drive connection failed: {e}")
            return False, str(e)


# Global instance
drive_uploader = DriveUploader()
