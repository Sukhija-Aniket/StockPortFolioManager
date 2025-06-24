from dataclasses import asdict, dataclass
from typing import Dict, Optional
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType


@dataclass
class SpreadsheetTask:
    spreadsheet_id: str
    spreadsheet_type: SpreadsheetType
    credentials: Optional[Dict] = None  # None for Excel, OAuth for Google Sheets
    title: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SpreadsheetTask':
        return cls(
            spreadsheet_id=data.get('spreadsheet_id'),
            spreadsheet_type=SpreadsheetType(data.get('spreadsheet_type')),
            credentials=data.get('credentials'),
            title=data.get('title')
        )
        
    
    def to_dict(self) -> Dict:
        """Convert SpreadsheetTask to dictionary for serialization"""
        data = asdict(self)
        # Convert enum to string for JSON serialization
        data['spreadsheet_type'] = self.spreadsheet_type.value
        return data