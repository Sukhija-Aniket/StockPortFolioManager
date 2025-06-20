"""
Google Sheets utilities for Stock Portfolio Manager
"""

import gspread
import requests
import os
import logging
import pandas as pd
import numpy as np
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from ..constants import CELL_RANGE

logger = logging.getLogger(__name__)

class SheetsManager:
    """Manages Google Sheets operations"""
    
    def __init__(self, credentials_file=None, credentials=None):
        self.credentials_file = credentials_file
        self.credentials = credentials
    
    def authenticate_and_get_sheets(self, credentials_file,spreadsheet_id, credentials=None, http=None):
        """Authenticate and get Google Sheets instance"""
        logger.info("Authenticating Sheets: %s", spreadsheet_id)
        
        if credentials is not None:
            logger.info("Authenticating using Credentials")
            try:
                credentials_obj = Credentials(**credentials)
                logger.info("credentials_obj: %s", credentials_obj.to_json())  
                # Use the custom HTTP client with disabled SSL validation
                # Create a Session that skips SSL checks
                session = AuthorizedSession(credentials_obj) 
                session.verify = False  # disable cert validation
                gc = gspread.Client(auth=credentials_obj, session=session)
                spreadsheet = gc.open_by_key(spreadsheet_id)
                logger.info("Authorized, this is the spreadsheet_id: %s", spreadsheet_id)
                return spreadsheet
            except Exception as e:
                logger.error("Unable to authorize spreadsheet %s, exiting...", e)
                raise RuntimeError(f"Authorization Failed for spreadsheets: {e}")
        else:
            logger.info("Authenticating using Service Account")
            gc = gspread.service_account(filename=credentials_file)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            return spreadsheet
    
    def read_data_from_sheets(self, spreadsheet, sheet_name):
        """Read data from Google Sheets"""
        sheet = spreadsheet.worksheet(sheet_name)
        data = sheet.get_all_values()
        if len(data) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    
    def format_background_sheets(self, spreadsheet, sheet, cell_range):
        """Format background of Google Sheets"""
        requests = [{
            "updateCells": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": int(cell_range.split(':')[0][1:]) - 1,
                    "endRowIndex": int(cell_range.split(':')[1][1:]),
                    "startColumnIndex": ord(cell_range.split(':')[0][0].upper()) - 65,
                    "endColumnIndex": ord(cell_range.split(':')[1][0].upper()) - 64,
                },
                "fields": "userEnteredFormat.backgroundColor",
            }
        }]
        spreadsheet.batch_update({"requests": requests})
    
    def initialize_sheets(self, spreadsheet, sheet_name):
        """Initialize Google Sheets"""
        sheet = spreadsheet.worksheet(sheet_name)
        sheet.clear() 
        self.format_background_sheets(spreadsheet, sheet, CELL_RANGE)    
        return sheet
    
    def display_and_format_sheets(self, sheet, data):
        """Display and format data in Google Sheets"""
        logger.info(f"Displaying and formatting data in {sheet.title}")
        
        try:
            # Convert numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')  # Convert string to numeric
            data[numeric_cols] = data[numeric_cols].round(4)
            
            headers = data.columns.tolist() 
            data_values = data.values.tolist() 

            # Update sheet with data
            sheet.update('A1', [headers])
            if data_values:
                sheet.insert_rows(data_values, 2)
            
            # Add formatting to headers
            num_columns = len(headers)
            if num_columns > 0:
                # Calculate header range safely
                if num_columns <= 26:
                    header_range = f'A1:{chr(64 + num_columns)}1'
                else:
                    # Handle columns beyond Z (AA, AB, etc.)
                    col_letter = self._get_column_letter(num_columns)
                    header_range = f'A1:{col_letter}1'
                
                try:
                    sheet.format(header_range, {"textFormat": {"bold": True}})
                except Exception as e:
                    logger.warning(f"Could not format headers: {e}")
                
                # Format numeric columns with proper number format
                if numeric_cols:
                    try:
                        # Format each numeric column individually to avoid range issues
                        for col_name in numeric_cols:
                            if col_name in headers:
                                col_index = headers.index(col_name)
                                if col_index < 26:
                                    col_letter = chr(65 + col_index)
                                else:
                                    col_letter = self._get_column_letter(col_index + 1)
                                
                                # Format the entire column
                                col_range = f'{col_letter}2:{col_letter}{len(data_values) + 1}'
                                number_format = {
                                    "numberFormat": {
                                        "type": "NUMBER",
                                        "pattern": "#,##0"
                                    }
                                }
                                sheet.format(col_range, number_format)
                    except Exception as e:
                        logger.warning(f"Could not format numeric columns: {e}")
            
            logger.info(f"Displaying and formatting data in {sheet.title} completed")
            
        except Exception as e:
            logger.error(f"Error in display_and_format_sheets: {e}")
            # Fallback: just update the data without formatting
            try:
                headers = data.columns.tolist() 
                data_values = data.values.tolist() 
                sheet.update('A1', [headers])
                if data_values:
                    sheet.insert_rows(data_values, 2)
                logger.info(f"Data updated without formatting for {sheet.title}")
            except Exception as fallback_error:
                logger.error(f"Fallback update also failed: {fallback_error}")
                raise
    
    def _get_column_letter(self, column_number):
        """Convert column number to letter (1=A, 27=AA, etc.)"""
        result = ""
        while column_number > 0:
            column_number, remainder = divmod(column_number - 1, 26)
            result = chr(65 + remainder) + result
        return result
    
    def update_sheet(self, spreadsheet, sheet_name, data, formatting_function=None):
        """Update Google Sheets with data"""
        logger.info("this message will be removed later!")
        sheet = self.initialize_sheets(spreadsheet, sheet_name)
        self.display_and_format_sheets(sheet, data)
        if formatting_function is not None:
            formatting_function(spreadsheet, sheet)
        logger.info(f"{sheet_name} updated Successfully!")
    
    def get_sheets_and_data(self, typ, credentials_file, spreadsheet_id, spreadsheet_file, credentials=None, http=None):
        """Get sheets and data based on type"""
        if typ == 'sheets':
            spreadsheet = self.authenticate_and_get_sheets(
                credentials_file, spreadsheet_id, credentials, http)
            worksheets = spreadsheet.worksheets()
            sheet_names = [worksheet.title for worksheet in worksheets]
            raw_data = self.read_data_from_sheets(spreadsheet, sheet_names[0])
        else:
            from .excel import ExcelManager
            excel_manager = ExcelManager()
            spreadsheet = excel_manager.load_workbook(spreadsheet_file)
            sheet_names = spreadsheet.sheetnames
            raw_data = excel_manager.read_data_from_excel(spreadsheet, sheet_names[0])

        return spreadsheet, sheet_names, raw_data
    
    def credentials_to_dict(self, credentials):
        """Convert credentials to dictionary"""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token or '',
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        } 