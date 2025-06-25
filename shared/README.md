# Stock Portfolio Shared Library

A shared Python library containing common utilities, models, and constants used across the Stock Portfolio Manager components.

## Installation

### For Development (Editable Install)
```bash
# From the shared directory
pip install -e .

# Or from the root directory
pip install -e ./shared
```

### For Production (Regular Install)
```bash
# From the shared directory
pip install .

# Or from the root directory
pip install ./shared
```

### From Git Repository
```bash
pip install git+https://github.com/Sukhija-Aniket/StockPortfolioManager.git#subdirectory=shared
```

## Usage

```python
from stock_portfolio_shared.models import SpreadsheetTask
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.constants.general_constants import BUY, SELL

# Use shared functionality
sheets_manager = SheetsManager()
```

## Development

### Building the Package
```bash
cd shared
python setup.py sdist bdist_wheel
```

### Publishing to PyPI (if needed)
```bash
pip install twine
twine upload dist/*
```

## Version Management

This package follows semantic versioning. When making changes:
1. Update the version in `setup.py`
2. Update the version in dependent components' requirements.txt
3. Tag the release in git

## Structure

- `constants/` - Shared constants and configuration
- `utils/` - Utility functions for sheets, excel, and data processing
- `models/` - Data models and structures

This package is shared between the backend and scripts services to avoid code duplication. 