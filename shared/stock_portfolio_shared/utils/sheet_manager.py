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
from .base_manager import BaseManager
from ..constants import BUY, CELL_RANGE
from ..utils.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class SheetsManager(BaseManager):
    """Manages Google Sheets operations"""
    
    def __init__(self, credentials):
        self.credentials = credentials
        self.data_processor = DataProcessor()
    
    def _get_spreadsheet(self,spreadsheet_id):
        """Authenticate and get Google Sheets instance"""
        logger.info("Authenticating Sheets: %s", spreadsheet_id)
        try:
            credentials_obj = Credentials(**self.credentials)
            # Use the custom HTTP client with disabled SSL validation
            # Create a Session that skips SSL checks
            session = AuthorizedSession(credentials_obj) 
            session.verify = False  # disable cert validation
            gc = gspread.Client(auth=credentials_obj, session=session)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            logger.info("Authorized, this is the spreadsheet_id: %s", spreadsheet_id)
            return spreadsheet
        except Exception as e:
            logger.error("Unable to authorize spreadsheet %s", e)
            raise RuntimeError(f"Authorization Failed for spreadsheets: {e}")
    
    def read_data(self, spreadsheet, sheet_name):
        """Read data from Google Sheets"""
        worksheets = spreadsheet.worksheets()
        sheet_names = [worksheet.title for worksheet in worksheets]
        if sheet_name not in sheet_names:
            raise ValueError(f"Sheet {sheet_name} not found in provided Spreadsheet")
        sheet = spreadsheet.worksheet(sheet_name)
        data = sheet.get_all_values()
        if len(data) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    
    def upload_data(self, input_data, spreadsheet_id, sheet_name, allow_duplicates=False):
        """Upload data to sheets"""
        try:
            spreadsheet = self.get_spreadsheet(spreadsheet_id, sheet_name)
            raw_data = self.read_data(spreadsheet, sheet_name)
            validated_input_data = self.validate_data(raw_data, input_data)
            if not allow_duplicates and self.data_processor.data_already_exists(raw_data, validated_input_data):
                logger.warning("Data already exists in Sheets, Skipping Upload")
                return
            raw_data = pd.concat([raw_data, validated_input_data], ignore_index=True)
            self._update_data(spreadsheet, sheet_name, raw_data)
            logger.info("Data uploaded successfully to Sheets")
        except Exception as e:
            logger.error(f"Error uploading data to sheets: {e}")
            raise
    
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
    
    def _initialize_sheets(self, spreadsheet, sheet_name):
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
    
    def _update_data(self, spreadsheet, sheet_name, data, formatting_function=None):
        """Update Google Sheets with data"""
        sheet = self._initialize_sheets(spreadsheet, sheet_name)
        self.display_and_format_sheets(sheet, data)
        if formatting_function is not None:
            formatting_function(spreadsheet, sheet)
        logger.info(f"{sheet_name} updated Successfully!")
    
    def get_sheet_names(self, spreadsheet_id):
        spreadsheet = self._get_spreadsheet(spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        sheet_names = [worksheet.title for worksheet in worksheets]
        return sheet_names
    
    def get_spreadsheet(self, spreadsheet_id):
        """Get sheets data"""
        spreadsheet = self._get_spreadsheet(spreadsheet_id)
        return spreadsheet
    
    def _get_backgroundColor_formatting_request(sheet, row_number, row_data, background_color):
        format_request = {
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": row_number - 1,
                    "endRowIndex": row_number,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(row_data)
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": background_color[0],
                            "green": background_color[1],
                            "blue": background_color[2]
                        }
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }
        return format_request
    
    def transDetails_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        requests = []
        for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
            transaction_type = row_data[6]
            if transaction_type == BUY:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            format_request = self._get_backgroundColor_formatting_request(sheet, row_number, row_data, background_color)
            requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def shareProfitLoss_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        requests = []
        for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
            remaining_shares = int(row_data[7])
            profit = float(row_data[9])
            if remaining_shares == 0:
                if profit > 0:
                    background_color = (0.8, 0.9, 1)
                else:
                    background_color = (1, 0.8, 0.8)
                format_request = self._get_backgroundColor_formatting_request(sheet,row_number, row_data, background_color)
                requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def dailyProfitLoss_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        requests = []
        for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
            if row_data[10] != "":
                if float(row_data[10]) > 0.0:
                    background_color = (0.8, 0.9, 1)
                else:
                    background_color = (1, 0.8, 0.8)
                format_request = self._get_backgroundColor_formatting_request(sheet,row_number, row_data, background_color)
                requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def taxation_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        requests = []
        for row_number, row_data in  enumerate(worksheet_data[1:], start=2):
            if (float(row_data[2]) + float(row_data[3]) + float(row_data[4])) >= 0:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            format_request = self._get_backgroundColor_formatting_request(sheet,row_number, row_data, background_color)
            requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def get_formatting_funcs(self, sheet_names):
        """Get formatting functions"""
        return {
            sheet_names[0]: None,
            sheet_names[1]: self.transDetails_formatting,
            sheet_names[2]: self.shareProfitLoss_formatting,
            sheet_names[3]: self.dailyProfitLoss_formatting,
            sheet_names[4]: self.taxation_formatting
        }
    
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