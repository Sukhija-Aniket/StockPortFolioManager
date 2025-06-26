from dataclasses import asdict, dataclass
from typing import Dict, Optional, Union
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType
from stock_portfolio_shared.models.depository_participant import DepositoryParticipant


@dataclass
class SpreadsheetTask:
    spreadsheet_id: str
    spreadsheet_type: SpreadsheetType
    credentials: Optional[Dict] = None  # None for Excel, OAuth for Google Sheets
    title: Optional[str] = None
    metadata: Optional[Dict] = None  # Store participant_name and other key information
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SpreadsheetTask':
        return cls(
            spreadsheet_id=data.get('spreadsheet_id'),
            spreadsheet_type=SpreadsheetType(data.get('spreadsheet_type')),
            credentials=data.get('credentials'),
            title=data.get('title'),
            metadata=data.get('metadata', {})
        )
        
    
    def to_dict(self) -> Dict:
        """Convert SpreadsheetTask to dictionary for serialization"""
        data = asdict(self)
        # Convert enum to string for JSON serialization
        data['spreadsheet_type'] = self.spreadsheet_type.value
        return data
    
    def get_participant_name(self) -> str:
        """Get participant name from metadata, default to ZERODHA"""
        if self.metadata and 'participant_name' in self.metadata:
            participant_value = self.metadata['participant_name']
            return DepositoryParticipant.from_string(participant_value).value
        return DepositoryParticipant.get_default().value
    
    def get_metadata_value(self, key: str, default=None):
        """Get a specific value from metadata"""
        if self.metadata and key in self.metadata:
            return self.metadata[key]
        return default