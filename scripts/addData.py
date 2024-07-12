import pandas as pd
import os
import sys
from datetime import datetime
import openpyxl

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)

from pythonPackage import utils
from pythonPackage.constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

spreadsheet_id = os.getenv('SPREADSHEET_ID')
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_file = os.path.join(parent_directory, 'assets', excel_file_name)
api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(parent_directory, 'secrets', api_key_file_name)

# Main Program
if __name__ == "__main__":
    
    # Taking Required user inputs
    input_file, typ = utils.get_args_and_input(sys.argv, excel_file_name, spreadsheet_id, env_file)
    input_file = utils.get_valid_path(input_file)
    
    # Handling User data and preparing raw data
    input_data = pd.read_csv(input_file)
    input_data = utils.format_add_data(input_data)
    spreadsheet, sheet_names, raw_data = utils.get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file)
    utils.data_already_exists(raw_data, input_data)
    raw_data = pd.concat([raw_data, input_data], ignore_index=True)
    
    # final updation
    updating_func = utils.get_updating_func(typ)
    updating_func(spreadsheet, sheet_names[0], raw_data)
    