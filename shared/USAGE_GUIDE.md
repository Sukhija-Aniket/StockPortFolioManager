# Stock Portfolio Shared Library - Usage Guide

## Overview

The `stock-portfolio-shared` library contains all the common utilities and constants used by both the backend and scripts services. This eliminates code duplication and ensures consistent behavior across services.

## Installation

### For Development (Editable Mode)
```bash
cd shared
pip install -e .
```

### For Production
```bash
pip install stock-portfolio-shared==0.1.0
```

## Usage Examples

### 1. Importing Constants
```python
from stock_portfolio_shared.constants.general_constants import BUY, SELL, DATA_TIME_FORMAT
from stock_portfolio_shared.constants.raw_constants import Raw_constants
from stock_portfolio_shared.constants.data_constants import Data_constants
from stock_portfolio_shared.constants.trans_details_constants import TransDetails_constants

# Use constants
print(f"Buy type: {BUY}")
print(f"Date format: {DATA_TIME_FORMAT}")
print(f"Date column: {Raw_constants.DATE}")
```

### 2. Using Sheets Manager
```python
from stock_portfolio_shared.utils.sheet_manager import SheetsManager

# Initialize sheets manager
sheets_manager = SheetsManager(credentials_file="path/to/credentials.json")

# Authenticate and get spreadsheet
spreadsheet = sheets_manager.authenticate_and_get_sheets(
    spreadsheet_id="your_spreadsheet_id",
    credentials=your_credentials
)

# Read data from sheets
data = sheets_manager.read_data_from_sheets(spreadsheet, "Sheet1")

# Update sheets
sheets_manager.update_sheet(spreadsheet, "Sheet1", your_data)
```

### 3. Using Excel Manager
```python
from stock_portfolio_shared.utils.excel_manager import ExcelManager

# Initialize excel manager
excel_manager = ExcelManager()

# Load workbook
workbook = excel_manager.load_workbook("path/to/file.xlsx")

# Read data
data = excel_manager.read_data_from_excel("path/to/file.xlsx", "Sheet1")

# Update excel
excel_manager.update_excel(workbook, "Sheet1", your_data)
```

### 4. Using Data Processor
```python
from stock_portfolio_shared.utils.data_processor import DataProcessor

# Process data
formatted_data = DataProcessor.format_add_data(input_data)

# Check for duplicates
DataProcessor.data_already_exists(raw_data, input_data)

# Get symbol from row
symbol = DataProcessor.get_symbol(row_data)

# Convert date format
date_str = DataProcessor.get_data_date("2025-06-19")
```

### 5. Using Common Utils
```python
from stock_portfolio_shared.utils.common import CommonUtils

# Update environment file
CommonUtils.update_env_file("API_KEY", "new_value", ".env")

# Parse command line arguments
input_file, typ, credentials = CommonUtils.get_args_and_input(
    args, excel_file_name, spreadsheet_id, env_file
)
```

## Migration Guide

### From Backend Utils
**Before:**
```python
from utils import authenticate_and_get_sheets, read_data_from_sheets
from stock_portfolio_shared.constants.general_constants import BUY, SELL

spreadsheet = authenticate_and_get_sheets(credentials_file, spreadsheet_id)
data = read_data_from_sheets(spreadsheet, sheet_name)
```

**After:**
```python
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.constants.general_constants import BUY, SELL

sheets_manager = SheetsManager(credentials_file)
spreadsheet = sheets_manager.authenticate_and_get_sheets(spreadsheet_id)
data = sheets_manager.read_data_from_sheets(spreadsheet, sheet_name)
```

### From Scripts Utils
**Before:**
```python
from utils import update_env_file, get_args_and_input
from stock_portfolio_shared.constants.general_constants import DATA_TIME_FORMAT

update_env_file(key, value, env_file)
input_file, typ, credentials = get_args_and_input(args, excel_file_name, spreadsheet_id, env_file)
```

**After:**
```python
from stock_portfolio_shared.utils.common import CommonUtils
from stock_portfolio_shared.constants.general_constants import DATA_TIME_FORMAT

CommonUtils.update_env_file(key, value, env_file)
input_file, typ, credentials = CommonUtils.get_args_and_input(args, excel_file_name, spreadsheet_id, env_file)
```

## Available Classes and Methods

### SheetsManager
- `authenticate_and_get_sheets(spreadsheet_id, credentials=None, http=None)`
- `read_data_from_sheets(spreadsheet, sheet_name)`
- `format_background_sheets(spreadsheet, sheet, cell_range)`
- `initialize_sheets(spreadsheet, sheet_name)`
- `display_and_format_sheets(sheet, data)`
- `update_sheet(spreadsheet, sheet_name, data, formatting_function=None)`
- `get_sheets_and_data(typ, credentials_file, spreadsheet_id, spreadsheet_file, credentials=None, http=None)`
- `credentials_to_dict(credentials)`

### ExcelManager
- `load_workbook(spreadsheet_file)`
- `read_data_from_excel(spreadsheet_file, sheet_name)`
- `format_background_excel(sheet, cell_range)`
- `display_and_format_excel(sheet, data)`
- `initialize_excel(spreadsheet, sheet_name)`
- `update_excel(spreadsheet, sheet_name, data, formatting_function=None)`
- `get_updating_func(typ)`

### DataProcessor
- `replace_out_of_range_floats(obj)`
- `get_symbol(row)`
- `get_data_date(date)`
- `get_data_quantity(row)`
- `get_net_amount(row)`
- `format_add_data(input_data)`
- `data_already_exists(raw_data, input_data)`
- `check_valid_path(path)`
- `get_valid_path(path)`

### CommonUtils
- `update_env_file(key, value, env_file)`
- `get_args_and_input(args, excel_file_name, spreadsheet_id, env_file)`

## Constants Available

### Basic Constants
- `BUY`, `SELL`
- `DATA_TIME_FORMAT`, `YFINANCE_DATE_FORMAT`, `ORDER_TIME_FORMAT`
- `BSE`, `NSE`
- `CELL_RANGE`

### Data Classes
- `Order_constants`
- `Data_constants`
- `Raw_constants`
- `TransDetails_constants`
- `ShareProfitLoss_constants`
- `DailyProfitLoss_constants`
- `Taxation_constants`

## Benefits

1. **Single Source of Truth**: All constants and utilities in one place
2. **Consistent Behavior**: Same logic across backend and scripts
3. **Easy Maintenance**: Changes only need to be made once
4. **Better Testing**: Can test shared functions independently
5. **Reduced Bugs**: Less chance of divergent implementations

## Development

### Adding New Functions
1. Add the function to the appropriate utility class
2. Update the `__init__.py` files if needed
3. Test the function
4. Update this guide

### Updating Constants
1. Modify the constants in the appropriate constants file
2. Test that all services still work
3. Update this guide if needed

## Testing

Run the test script to verify everything works:
```bash
cd shared
python test_shared_library.py
```

## Troubleshooting

### Import Errors
- Ensure the package is installed: `pip install -e .`
- Check that you're in the correct virtual environment
- Verify the import path is correct

### SSL Certificate Issues
The shared library includes SSL workarounds for Google Sheets authentication. If you encounter SSL issues, the `SheetsManager` class handles this automatically.

### Version Conflicts
If you encounter version conflicts, check the `setup.py` file for the required dependencies and ensure they're compatible with your project. 