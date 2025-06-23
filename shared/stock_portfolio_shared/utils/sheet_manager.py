"""
Google Sheets utilities for Stock Portfolio Manager
"""

import gspread
import logging
import pandas as pd
import numpy as np
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
from .base_manager import BaseManager
from ..constants.general_constants import BUY, CELL_RANGE
from ..constants.trans_details_constants import TransDetails_constants
from ..constants.raw_constants import Raw_constants
from ..constants.share_profit_loss_constants import ShareProfitLoss_constants
from ..constants.daily_profit_loss_constants import DailyProfitLoss_constants
from ..constants.taxation_constants import Taxation_constants
from ..utils.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class SheetsManager(BaseManager):
    """Manages Google Sheets operations"""
    
    def _get_column_index(self, headers, column_name):
        """Get column index by name"""
        try:
            return headers.index(column_name)
        except ValueError:
            logger.warning(f"Column '{column_name}' not found in headers: {headers}")
            return None
    
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
    
    def add_data(self, input_data, spreadsheet, sheet_name, allow_duplicates=False, formatting_function=None):
        """Upload data to sheets"""
        try:
            raw_data = self.read_data(spreadsheet, sheet_name)
            validated_input_data = self.validate_data(raw_data, input_data)
            if not allow_duplicates and DataProcessor.data_already_exists(raw_data, validated_input_data):
                logger.warning("Data already exists in Sheets, Skipping Upload")
                return
            raw_data = pd.concat([raw_data, validated_input_data], ignore_index=True)
            self.update_data(spreadsheet, sheet_name, raw_data, formatting_function)
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
            data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')  # Keep using to_numeric here instead of DataProcessor.safe_numeric
            data[numeric_cols] = data[numeric_cols].round(4)
            
            
            headers = data.columns.tolist() 
            data_values = data.values.tolist() 

            # Update sheet with data
            sheet.update('A1', [headers])
            if data_values:
                sheet.insert_rows(data_values, 2)
            
            # Prepare batch formatting requests
            formatting_requests = []
            
            # Add formatting to headers
            num_columns = len(headers)
            if num_columns > 0:
                # Header formatting request
                header_format_request = {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet.id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_columns
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat.textFormat.bold"
                    }
                }
                formatting_requests.append(header_format_request)
                
                # Format numeric columns with proper number format
                if numeric_cols:
                    for col_name in numeric_cols:
                        if col_name in headers:
                            col_index = headers.index(col_name)
                            
                            # Number format request for numeric columns
                            number_format_request = {
                                "repeatCell": {
                                    "range": {
                                        "sheetId": sheet.id,
                                        "startRowIndex": 1,  # Start from row 2 (after headers)
                                        "endRowIndex": len(data_values) + 1,
                                        "startColumnIndex": col_index,
                                        "endColumnIndex": col_index + 1
                                    },
                                    "cell": {
                                        "userEnteredFormat": {
                                            "numberFormat": {
                                                "type": "NUMBER",
                                                "pattern": "#,##0.00"
                                            }
                                        }
                                    },
                                    "fields": "userEnteredFormat.numberFormat"
                                }
                            }
                            formatting_requests.append(number_format_request)
            
            # Execute all formatting requests in one batch
            if formatting_requests:
                try:
                    sheet.spreadsheet.batch_update({"requests": formatting_requests})
                    logger.info(f"Batch formatting completed for {sheet.title}")
                except Exception as e:
                    logger.warning(f"Could not apply batch formatting: {e}")
            
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
    
    def update_data(self, spreadsheet, sheet_name, data, formatting_function=None):
        """Update Google Sheets with data"""
        sheet = self._initialize_sheets(spreadsheet, sheet_name)
        self.display_and_format_sheets(sheet, data)
        if formatting_function is not None:
            formatting_function(spreadsheet, sheet)
        logger.info(f"{sheet_name} updated Successfully!")
    
    def get_sheet_names(self, spreadsheet_task: SpreadsheetTask):
        spreadsheet = self.get_spreadsheet(spreadsheet_task)
        worksheets = spreadsheet.worksheets()
        sheet_names = [worksheet.title for worksheet in worksheets]
        return sheet_names
    
    def get_spreadsheet(self, spreadsheet_task: SpreadsheetTask):
        """Get sheets data"""
        logger.info("Authenticating Sheets: %s", spreadsheet_task.spreadsheet_id)
        try:
            credentials_obj = Credentials(**spreadsheet_task.credentials)
            # Use the custom HTTP client with disabled SSL validation
            # Create a Session that skips SSL checks
            session = AuthorizedSession(credentials_obj) 
            session.verify = False  # disable cert validation
            gc = gspread.Client(auth=credentials_obj, session=session)
            spreadsheet = gc.open_by_key(spreadsheet_task.spreadsheet_id)
            logger.info("Authorized, this is the spreadsheet_id: %s", spreadsheet_task.spreadsheet_id)
            return spreadsheet
        except Exception as e:
            logger.error("Unable to authorize spreadsheet %s", e)
            raise RuntimeError(f"Authorization Failed for spreadsheets: {e}")
    
    def _get_backgroundColor_formatting_request(self,sheet, row_number, row_data, background_color):
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
        if len(worksheet_data) < 2:
            return
            
        # Convert to pandas DataFrame
        headers = worksheet_data[0]
        data_values = worksheet_data[1:]
        df = pd.DataFrame(data_values, columns=headers)
        
        # Check if required columns exist
        if TransDetails_constants.TRANSACTION_TYPE not in df.columns:
            logger.error(f"Transaction Type column not found in headers: {headers}")
            return
            
        requests = []
        for row_number, row in df.iterrows():
            try:
                transaction_type = row[TransDetails_constants.TRANSACTION_TYPE] if row[TransDetails_constants.TRANSACTION_TYPE] is not None else ''
            except (ValueError, TypeError):
                logger.warning(f"Invalid row data: {row}")
                continue
                
            if transaction_type == BUY:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            # Convert row back to list for formatting
            row_data = row.tolist()
            format_request = self._get_backgroundColor_formatting_request(sheet, row_number + 2, row_data, background_color)
            requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def shareProfitLoss_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        if len(worksheet_data) < 2:
            return
            
        # Convert to pandas DataFrame
        headers = worksheet_data[0]
        data_values = worksheet_data[1:]
        df = pd.DataFrame(data_values, columns=headers)
        
        # Check if required columns exist
        if ShareProfitLoss_constants.SHARES_REMAINING not in df.columns or ShareProfitLoss_constants.NET_PROFIT not in df.columns:
            logger.error(f"Required columns not found in headers: {headers}")
            return
            
        requests = []
        for row_number, row in df.iterrows():
            try:
                remaining_shares = DataProcessor.safe_numeric(row[ShareProfitLoss_constants.SHARES_REMAINING])
                profit = DataProcessor.safe_numeric(row[ShareProfitLoss_constants.NET_PROFIT])
            except (ValueError, TypeError):
                logger.warning(f"Invalid row data: {row}")
                continue
                
            if abs(remaining_shares) < 0.01:  # Check if effectively zero (handles floating point precision)
                if profit > 0:
                    background_color = (0.8, 0.9, 1)
                else:
                    background_color = (1, 0.8, 0.8)
                # Convert row back to list for formatting
                row_data = row.tolist()
                format_request = self._get_backgroundColor_formatting_request(sheet, row_number + 2, row_data, background_color)
                requests.append(format_request)
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def dailyProfitLoss_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        if len(worksheet_data) < 2:
            return
            
        # Convert to pandas DataFrame
        headers = worksheet_data[0]
        data_values = worksheet_data[1:]
        df = pd.DataFrame(data_values, columns=headers)
        
        # Check if required columns exist
        if DailyProfitLoss_constants.DAILY_SPENDINGS not in df.columns:
            logger.error(f"Daily Spendings column not found in headers: {headers}")
            return
            
        requests = []
        for row_number, row in df.iterrows():
            try:
                daily_spendings = row[DailyProfitLoss_constants.DAILY_SPENDINGS] if row[DailyProfitLoss_constants.DAILY_SPENDINGS] is not None else ''
            except (ValueError, TypeError):
                logger.warning(f"Invalid row data: {row}")
                continue
                
            if daily_spendings != "":
                try:
                    spendings_value = DataProcessor.safe_numeric(daily_spendings)
                    if spendings_value > 0.0:
                        background_color = (0.8, 0.9, 1)
                    else:
                        background_color = (1, 0.8, 0.8)
                    # Convert row back to list for formatting
                    row_data = row.tolist()
                    format_request = self._get_backgroundColor_formatting_request(sheet, row_number + 2, row_data, background_color)
                    requests.append(format_request)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid daily spendings value: {daily_spendings}")
                    continue
        if len(requests) > 0:
            spreadsheet.batch_update({"requests": requests})
    
    def taxation_formatting(self, spreadsheet, sheet):
        worksheet_data = sheet.get_all_values()
        if len(worksheet_data) < 2:
            return
            
        # Convert to pandas DataFrame
        headers = worksheet_data[0]
        data_values = worksheet_data[1:]
        df = pd.DataFrame(data_values, columns=headers)
        
        # Check if required columns exist
        required_columns = [Taxation_constants.LTCG, Taxation_constants.STCG, Taxation_constants.INTRADAY_INCOME]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Required taxation columns not found in headers: {missing_columns}")
            return
            
        requests = []
        for row_number, row in df.iterrows():
            try:
                ltcg = DataProcessor.safe_numeric(row[Taxation_constants.LTCG])
                stcg = DataProcessor.safe_numeric(row[Taxation_constants.STCG])
                intraday_income = DataProcessor.safe_numeric(row[Taxation_constants.INTRADAY_INCOME])
            except (ValueError, TypeError):
                logger.warning(f"Invalid row data: {row}")
                continue
                
            if (ltcg + stcg + intraday_income) >= 0:
                background_color = (0.8, 0.9, 1)
            else:
                background_color = (1, 0.8, 0.8)
            # Convert row back to list for formatting
            row_data = row.tolist()
            format_request = self._get_backgroundColor_formatting_request(sheet, row_number + 2, row_data, background_color)
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