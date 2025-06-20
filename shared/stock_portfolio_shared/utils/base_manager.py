from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List
import pandas as pd

class BaseManager(ABC):
    """Base class for spreadsheet managers"""
    
    @abstractmethod
    def authenticate_and_get_spreadsheet(self, credentials_file: str, spreadsheet_id: str, 
                                       credentials: Dict = None) -> Any:
        """Authenticate and get spreadsheet instance"""
        pass
    
    @abstractmethod
    def read_data(self, spreadsheet: Any, sheet_name: str) -> pd.DataFrame:
        """Read data from spreadsheet"""
        pass
    
    @abstractmethod
    def update(self, spreadsheet: Any, sheet_name: str, data: pd.DataFrame, 
                    formatting_func: Callable = None) -> None:
        """Update sheet with data and optional formatting"""
        pass
    
    @abstractmethod
    def get_formatting_funcs(self, sheet_names: List[str]) -> Dict[str, Callable]:
        """Get formatting functions for this manager type"""
        pass
    
    @abstractmethod
    def upload_data(self, file_path: str, spreadsheet_id: str, creds: Dict, http: Any) -> None:
        """Upload data to spreadsheet"""
        pass