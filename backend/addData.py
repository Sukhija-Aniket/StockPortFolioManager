import pandas as pd
import os
import sys


scripts_directory = os.path.dirname(__file__)

from utils import *
from constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(scripts_directory, 'secrets', '.env')
load_dotenv(env_file)

spreadsheet_id = os.getenv('SPREADSHEET_ID')
excel_file_name = os.getenv('EXCEL_FILE_NAME')
spreadsheet_file = os.path.join(scripts_directory, 'assets', excel_file_name)
api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(scripts_directory, 'secrets', api_key_file_name)

def reload_env_file(env_file):
    # Clear existing environment variables that were set by dotenv
    for key in list(os.environ):
        if key.startswith("SPREADSHEET_ID") or key.startswith("EXCEL_FILE_NAME"):
            del os.environ[key]
    
    # Reload environment variables from the .env file
    load_dotenv(env_file)

def update():
    reload_env_file(env_file)
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    excel_file_name = os.getenv('EXCEL_FILE_NAME')
    spreadsheet_file = os.path.join(scripts_directory, 'assets', excel_file_name)
    return spreadsheet_id, excel_file_name, spreadsheet_file

# Main Program
if __name__ == "__main__":
    
    # Taking Required user inputs
    input_file, typ, credentials = get_args_and_input(sys.argv, excel_file_name, spreadsheet_id, env_file)
    print("old spreadsheet id: ", spreadsheet_id)
    spreadsheet_id, excel_file_name, spreadsheet_file = update()
    print("new spreadsheet id: ", spreadsheet_id)
    input_file = get_valid_path(input_file)
    
    # Handling User data and preparing raw data
    input_data = pd.read_csv(input_file)
    input_data = format_add_data(input_data)
    spreadsheet, sheet_names, raw_data = get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file, credentials)
    data_already_exists(raw_data, input_data)
    raw_data = pd.concat([raw_data, input_data], ignore_index=True)
    
    # final updation
    updating_func = get_updating_func(typ)
    updating_func(spreadsheet, sheet_names[0], raw_data)
    