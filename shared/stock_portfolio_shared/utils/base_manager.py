from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List
import pandas as pd
import logging

from ..models.spreadsheet_task import SpreadsheetTask

logger = logging.getLogger(__name__)

class BaseManager(ABC):
    """Base class for spreadsheet managers"""
    
    @abstractmethod
    def get_spreadsheet(self, spreadsheet_task: SpreadsheetTask) -> Any:
        """Authenticate and get spreadsheet instance"""
        pass
    
    @abstractmethod
    def get_sheet_names(self, spreadsheet_task: SpreadsheetTask) -> List[str]:
        """Get sheet names from spreadsheet"""
        pass
    
    @abstractmethod
    def read_data(self, spreadsheet: Any, sheet_name: str) -> pd.DataFrame:
        """Read data from spreadsheet"""
        pass
    
    @abstractmethod
    def get_formatting_funcs(self, sheet_names: List[str]) -> Dict[str, Callable]:
        """Get formatting functions for this manager type"""
        pass
    
    @abstractmethod # TODO: use spreadsheet object here instead of spreadsheet_id
    def add_data(self, input_data: pd.DataFrame, spreadsheet: str, sheet_name: str, formatting_function: Callable) -> None:
        """Upload data to spreadsheet"""
        pass
    
    @abstractmethod
    def update_data(self, spreadsheet: str, sheet_name: str, data: pd.DataFrame, formatting_function: Callable) -> None:
        """Update data in spreadsheet"""
        pass
    
    def validate_data(self, raw_data, input_data):
        """Validate that raw_data and input_data have compatible columns"""
        if not raw_data.empty and not input_data.empty:
            raw_columns = set(raw_data.columns)
            input_columns = set(input_data.columns)
            
            if raw_columns != input_columns:
                missing_in_input = raw_columns - input_columns
                missing_in_raw = input_columns - raw_columns
                
                error_msg = "Column mismatch between existing data and new data:"
                if missing_in_input:
                    error_msg += f"\nColumns missing in new data: {list(missing_in_input)}"
                if missing_in_raw:
                    error_msg += f"\nColumns missing in existing data: {list(missing_in_raw)}"
                
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Ensure column order matches
            validated_input_data = input_data[raw_data.columns.tolist()]
            logger.info("Column compatibility check passed")
            return validated_input_data
        else:
            logger.info("Skipping validation - one or both DataFrames are empty")
            return input_data