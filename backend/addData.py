import pandas as pd
import os
import sys
import logging
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

scripts_directory = os.path.dirname(__file__)

from utils import *
from constants import *

# Important Information
from dotenv import load_dotenv
env_file = os.path.join(scripts_directory, 'secrets', '.env')
load_dotenv(env_file)

api_key_file_name = 'tradingprojects-apiKey.json'
credentials_file = os.path.join(scripts_directory, 'secrets', api_key_file_name)

def upload_data(file_path, typ, spreadsheet_id, creds, http): 
    valid_path = check_valid_path(file_path)
    if valid_path:
        # Handling User data and preparing raw data
        print("Provided file Path: " + file_path)
        input_data = pd.read_csv(file_path)
        final_input_data = format_add_data(input_data)
        
        # Replace out-of-range float values
        # input_data = replace_out_of_range_floats(input_data.to_dict(orient='records'))
        
        spreadsheet, sheet_names, raw_data = get_sheets_and_data(typ, credentials_file, spreadsheet_id, None, creds, http) if typ == "sheets" else get_sheets_and_data(typ, credentials_file, None, spreadsheet_id, creds, http)
        data_already_exists(raw_data, final_input_data)
        raw_data = pd.concat([raw_data, final_input_data], ignore_index=True)
        
        # final updation
        updating_func = get_updating_func(typ)
        updating_func(spreadsheet, sheet_names[0], raw_data)
    else:
        print(f"Invalid path: {file_path}")
        return
    