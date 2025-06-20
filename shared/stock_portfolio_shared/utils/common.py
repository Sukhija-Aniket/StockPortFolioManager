"""
Common utilities for Stock Portfolio Manager
"""

import json
import logging
from ..constants import *

logger = logging.getLogger(__name__)

class CommonUtils:
    """Common utility functions"""
    
    @staticmethod
    def update_env_file(key, value, env_file):
        """Update environment file with new key-value pair"""
        logger.info("updating env file")
        with open(env_file, 'r') as file:
            lines = file.readlines()    

        updated_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                line = f"{key}={value}\n"
            updated_lines.append(line)

        logger.info("Lines updated are: %s", updated_lines)
        with open(env_file, 'w') as file:
            file.writelines(updated_lines)
    
    @staticmethod
    def get_args_and_input(args, excel_file_name, spreadsheet_id, env_file):
        """Parse command line arguments and get user input"""
        input_file = None
        value = ''
        key = 'EXCEL_FILE_NAME'
        credentials = None
        logger.info("Args length: %d and Args: %s", len(args), args)
        
        if len(args) > 4:
            credentials = json.loads(args[4])       
        if len(args) > 3:
            value = args[3]
        if len(args) > 2:
            typ = args[2].lower()
            if typ == 'sheets':
                key = 'SPREADSHEET_ID'
            input_file = args[1]
            if input_file == 'None':
                input_file = None
        else:
            if len(args) > 1:
                input_file = args[1]
            else:
                input_file = input("Please enter the absolute path of the file downloaded from Zerodha: ")
            logger.info("\nPlease select 'excel' or 'sheets, leave empty to use excel as default")
            typ = input("Enter your choice: ")
            typ = typ.lower()
            if (typ == 'excel' or typ == ''):
                logger.info(
                    f"{excel_file_name} is the default file, enter name below if you wish to change it, leave empty otherwise")
                value = input("Enter your choice: ")

            elif (typ == 'sheets'):
                logger.info(f"{spreadsheet_id} is the default google sheet, enter spreadsheet_id below if you wish to change it, leave empty otherwise")
                value = input("Enter your choice: ")
                key = 'SPREADSHEET_ID'

        if value is not None and value != '':
            CommonUtils.update_env_file(key, value, env_file)

        return input_file, typ, credentials
    
    @staticmethod
    def extract_spreadsheet_id(url):
        """Extract spreadsheet ID from Google Sheets URL"""
        if '/d/' in url:
            return url.split('/d/')[1].split('/')[0]
        return None 