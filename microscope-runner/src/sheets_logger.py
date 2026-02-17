"""Google Sheets logging for microscope captures."""

import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import settings

logger = logging.getLogger(__name__)


class SheetsLogger:
    """Logs microscope capture data to Google Sheets."""
    
    def __init__(self):
        self.credentials_path = settings.drive_credentials_path
        self.spreadsheet_id = settings.sheets_spreadsheet_id
        self.sheet_name = 'Microscope_Captures'
        self._service = None
    
    def _get_service(self):
        """Get or create the Sheets service."""
        if self._service is None:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self._service = build('sheets', 'v4', credentials=creds)
        return self._service
    
    def log_capture(
        self,
        job_number: str,
        local_path: str,
        drive_file_id: Optional[str] = None,
        drive_url: Optional[str] = None,
        material_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        tuning_session_id: Optional[str] = None,
        iteration: Optional[int] = None,
        notes: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Log a capture to the Microscope_Captures sheet.
        
        Returns:
            Tuple of (success, capture_id)
        """
        try:
            service = self._get_service()
            
            # Generate unique capture ID
            capture_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().isoformat()
            
            # Extract parameters
            params = parameters or {}
            mets = metrics or {}
            
            # Build row data matching sheet columns
            row = [
                capture_id,                          # capture_id
                timestamp,                           # timestamp
                job_number,                          # job_number
                material_name or '',                 # material_name
                drive_file_id or '',                 # image_drive_id
                drive_url or '',                     # image_url
                local_path,                          # image_local_path
                params.get('feedRate_mm_min', ''),   # feedRate_mm_min
                params.get('minPower_pct', ''),      # minPower_pct
                params.get('maxPower_pct', ''),      # maxPower_pct
                params.get('quality', ''),           # quality
                params.get('whiteClip', ''),         # whiteClip
                params.get('contrast', ''),          # contrast
                params.get('brightness', ''),        # brightness
                '',                                  # manual_score (filled by human later)
                mets.get('metric_contrast', ''),     # metric_contrast (auto-computed)
                mets.get('metric_sharpness', ''),    # metric_sharpness (auto-computed)
                mets.get('metric_composite', ''),    # metric_composite (auto-computed)
                tuning_session_id or '',             # tuning_session_id
                iteration if iteration is not None else '',  # iteration
                notes or ''                          # notes
            ]
            
            # Append row to sheet
            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:U',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row]}
            ).execute()
            
            logger.info(f"Logged capture to sheet: {capture_id}")
            return True, capture_id
            
        except Exception as e:
            logger.error(f"Failed to log capture to sheet: {e}")
            return False, ''
    
    def update_metrics(
        self,
        capture_id: str,
        manual_score: Optional[int] = None,
        metric_contrast: Optional[float] = None,
        metric_sharpness: Optional[float] = None,
        metric_composite: Optional[float] = None
    ) -> bool:
        """Update quality metrics for a capture."""
        try:
            service = self._get_service()
            
            # Find the row with this capture_id
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:A'
            ).execute()
            
            values = result.get('values', [])
            row_index = None
            for i, row in enumerate(values):
                if row and row[0] == capture_id:
                    row_index = i + 1  # 1-indexed for Sheets
                    break
            
            if row_index is None:
                logger.warning(f"Capture ID not found: {capture_id}")
                return False
            
            # Update metrics columns (O, P, Q, R = columns 15-18)
            updates = []
            if manual_score is not None:
                updates.append({
                    'range': f'{self.sheet_name}!O{row_index}',
                    'values': [[manual_score]]
                })
            if metric_contrast is not None:
                updates.append({
                    'range': f'{self.sheet_name}!P{row_index}',
                    'values': [[metric_contrast]]
                })
            if metric_sharpness is not None:
                updates.append({
                    'range': f'{self.sheet_name}!Q{row_index}',
                    'values': [[metric_sharpness]]
                })
            if metric_composite is not None:
                updates.append({
                    'range': f'{self.sheet_name}!R{row_index}',
                    'values': [[metric_composite]]
                })
            
            if updates:
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={
                        'valueInputOption': 'RAW',
                        'data': updates
                    }
                ).execute()
                logger.info(f"Updated metrics for capture: {capture_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to Google Sheets."""
        try:
            service = self._get_service()
            result = service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            logger.info(f"Connected to spreadsheet: {result.get('properties', {}).get('title')}")
            return True, None
        except Exception as e:
            logger.error(f"Sheets connection failed: {e}")
            return False, str(e)


# Global instance
sheets_logger = SheetsLogger()
