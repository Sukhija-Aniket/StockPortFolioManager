# Stock Portfolio Shared Library

Shared utilities and constants for the Stock Portfolio Manager application.

## Installation

For development, install in editable mode:

```bash
pip install -e .
```

## Usage

```python
from stock_portfolio_shared.constants import *
from stock_portfolio_shared.utils.sheets import SheetsManager
from stock_portfolio_shared.utils.excel import ExcelManager
from stock_portfolio_shared.utils.data_processing import DataProcessor
```

## Structure

- `constants/` - Shared constants and configuration
- `utils/` - Utility functions for sheets, excel, and data processing
- `models/` - Data models and structures

## Development

This package is shared between the backend and scripts services to avoid code duplication. 