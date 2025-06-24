import os
import logging
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google_auth_httplib2
import httplib2
import certifi
from config import Config

logger = logging.getLogger(__name__)

class GoogleService:
    """Service class for handling Google API interactions"""
    
    def __init__(self):
        self.http = httplib2.Http(ca_certs=certifi.where(), disable_ssl_certificate_validation=True)
        self.flow = Flow.from_client_secrets_file(
            Config.GOOGLE_CREDENTIALS_FILE,
            scopes=Config.GOOGLE_SCOPES,
            redirect_uri=f"http://{Config.BACKEND_SERVICE}/auth/oauth2callback"
        )
    
    def get_authorization_url(self, state):
        """Get Google OAuth authorization URL"""
        try:
            authorization_url, state = self.flow.authorization_url(access_type='offline', include_granted_scopes='true')
            return authorization_url, state
        except Exception as e:
            logger.error(f"Error getting authorization URL: {e}")
            raise
    
    def exchange_code_for_token(self, authorization_response):
        """Exchange authorization code for access token"""
        try:
            self.flow.fetch_token(authorization_response=authorization_response)
            return self.flow.credentials
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    def get_user_profile(self, credentials):
        """Get user profile from Google"""
        try:
            authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=self.http)
            service = build('oauth2', 'v2', http=authorized_http)
            profile = service.userinfo().get().execute()
            return profile
        except HttpError as e:
            logger.error(f"Error getting user profile: {e}")
            raise
    
    def create_spreadsheet_service(self, credentials):
        """Create Google Sheets service"""
        try:
            authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=self.http)
            return build('sheets', 'v4', http=authorized_http)
        except Exception as e:
            logger.error(f"Error creating sheets service: {e}")
            raise
    
    def create_drive_service(self, credentials):
        """Create Google Drive service"""
        try:
            authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=self.http)
            return build('drive', 'v3', http=authorized_http)
        except Exception as e:
            logger.error(f"Error creating drive service: {e}")
            raise
    
    def create_spreadsheet(self, service, title):
        """Create a new Google Spreadsheet"""
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            sheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
            return sheet.get('spreadsheetId')
        except HttpError as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise
    
    def setup_spreadsheet_sheets(self, service, spreadsheet_id):
        """Setup initial sheets in the spreadsheet"""
        try:
            requests = [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": 0,
                            "title": "Transactions"
                        },
                        "fields": "title"
                    }
                }
            ]
            
            titles = ["TransDetails Sorted", "Share Profit/Loss", "Daily Profit/Loss", "Taxation"]
            for title in titles:
                requests.append({
                    "addSheet": {
                        "properties": {
                            "title": title
                        }
                    }
                })
            
            body = {"requests": requests}
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        except HttpError as e:
            logger.error(f"Error setting up spreadsheet sheets: {e}")
            raise
    
    def delete_spreadsheet(self, drive_service, spreadsheet_id):
        """Delete a Google Spreadsheet"""
        try:
            drive_service.files().delete(fileId=spreadsheet_id).execute()
        except HttpError as e:
            logger.error(f"Error deleting spreadsheet: {e}")
            raise 