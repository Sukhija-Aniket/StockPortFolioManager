import logging
from datetime import datetime
from extensions import db
from models.spreadsheet import Spreadsheet
from models.user import User
from services.google_service import GoogleService
from stock_portfolio_shared.utils.sheet_manager import SheetsManager

logger = logging.getLogger(__name__)

class SpreadsheetService:
    """Service class for handling spreadsheet-related operations"""
    
    def __init__(self):
        self.google_service = GoogleService()
        self.sheets_manager = SheetsManager()
    
    def credentials_to_dict(self, credentials):
        """Convert credentials to dictionary using shared library"""
        return self.sheets_manager.credentials_to_dict(credentials)
    
    def get_user_spreadsheets(self, user_email):
        """Get all spreadsheets for a user"""
        try:
            user = User.query.filter_by(email=user_email).first()
            if not user:
                return None
            
            spreadsheets = Spreadsheet.query.filter_by(user_id=user.id).all()
            return [spreadsheet.to_dict() for spreadsheet in spreadsheets]
        except Exception as e:
            logger.error(f"Error getting user spreadsheets: {e}")
            raise
    
    def create_spreadsheet(self, user_id, title, credentials):
        """Create a new spreadsheet for user"""
        try:
            # Convert credentials dict to Credentials object
            from google.oauth2.credentials import Credentials
            creds_obj = Credentials(**credentials)
            
            # Create Google services
            sheets_service = self.google_service.create_spreadsheet_service(creds_obj)
            drive_service = self.google_service.create_drive_service(creds_obj)
            
            # Create spreadsheet in Google
            spreadsheet_id = self.google_service.create_spreadsheet(sheets_service, title)
            
            # Setup initial sheets
            self.google_service.setup_spreadsheet_sheets(sheets_service, spreadsheet_id)
            
            # Save to database
            spreadsheet = Spreadsheet(
                title=title,
                user_id=user_id,
                date_created=datetime.now().date().isoformat(),
                spreadsheet_id=spreadsheet_id
            )
            db.session.add(spreadsheet)
            db.session.commit()
            
            logger.info(f"Created spreadsheet: {title} with ID: {spreadsheet_id}")
            return spreadsheet.to_dict()
            
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            db.session.rollback()
            raise
    
    def delete_spreadsheet(self, user_id, spreadsheet_id, credentials):
        """Delete a spreadsheet"""
        try:
            # Check if spreadsheet belongs to user
            spreadsheet = Spreadsheet.query.filter_by(
                spreadsheet_id=spreadsheet_id,
                user_id=user_id
            ).first()
            
            if not spreadsheet:
                raise ValueError("Spreadsheet not found or access denied")
            
            # Convert credentials dict to Credentials object
            from google.oauth2.credentials import Credentials
            creds_obj = Credentials(**credentials)
            
            # Create Google Drive service
            drive_service = self.google_service.create_drive_service(creds_obj)
            
            # Delete from Google
            self.google_service.delete_spreadsheet(drive_service, spreadsheet_id)
            
            # Delete from database
            db.session.delete(spreadsheet)
            db.session.commit()
            
            logger.info(f"Deleted spreadsheet: {spreadsheet.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting spreadsheet: {e}")
            db.session.rollback()
            raise
    
    def get_spreadsheet_by_id(self, spreadsheet_id, user_id=None):
        """Get spreadsheet by ID, optionally checking user ownership"""
        try:
            query = Spreadsheet.query.filter_by(spreadsheet_id=spreadsheet_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            return query.first()
        except Exception as e:
            logger.error(f"Error getting spreadsheet by ID: {e}")
            raise 