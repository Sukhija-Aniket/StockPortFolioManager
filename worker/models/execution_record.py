from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.sql import func
from database import Base
from datetime import datetime, timezone
import hashlib
import logging

logger = logging.getLogger(__name__)

class ExecutionRecord(Base):
    """Model for storing worker execution records"""
    __tablename__ = 'execution_records'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core tracking fields
    execution_time = Column(DateTime, nullable=False)
    worker_id = Column(String(100), nullable=False, index=True)
    data_hash = Column(String(64), nullable=True, index=True)
    spreadsheet_id = Column(String(100), nullable=False, index=True)
    
    # Additional useful fields
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed
    processing_duration = Column(Float)
    rows_processed = Column(Integer)
    error_message = Column(Text)
    
    # Metadata fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Performance metrics
    memory_usage = Column(Float)  # MB
    cpu_usage = Column(Float)  # percentage
    
    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_time = Column(DateTime)
    
    def __repr__(self):
        return f'<ExecutionRecord {self.worker_id} - {self.spreadsheet_id} - {self.status}>'
    
    def to_dict(self):
        """Convert execution record to dictionary"""
        return {
            'id': self.id,
            'execution_time': self.execution_time.isoformat() if self.execution_time else None,
            'worker_id': self.worker_id,
            'data_hash': self.data_hash,
            'spreadsheet_id': self.spreadsheet_id,
            'status': self.status,
            'processing_duration': self.processing_duration,
            'rows_processed': self.rows_processed,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'last_retry_time': self.last_retry_time.isoformat() if self.last_retry_time else None
        }
    
    @staticmethod
    def generate_data_hash(data):
        """Generate hash for data to detect duplicates"""
        if isinstance(data, str):
            return hashlib.sha256(data.encode()).hexdigest()
        elif hasattr(data, 'to_string'):
            return hashlib.sha256(data.to_string().encode()).hexdigest()
        else:
            return hashlib.sha256(str(data).encode()).hexdigest()
    
    def is_duplicate(self, other_record):
        """Check if this execution is a duplicate of another"""
        # If either record has no data_hash, they can't be duplicates
        if not self.data_hash or not other_record.data_hash:
            return False
        return (self.data_hash == other_record.data_hash and 
                self.spreadsheet_id == other_record.spreadsheet_id)
    
    def can_retry(self):
        """Check if this execution can be retried"""
        return self.retry_count < self.max_retries and self.status == 'failed'
    
    def mark_completed(self, duration=None, rows_processed=None):
        """Mark execution as completed"""
        self.status = 'completed'
        self.processing_duration = duration
        self.rows_processed = rows_processed
    
    def mark_failed(self, error_message=None):
        """Mark execution as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
    
    def update_retry_info(self, attempt: int):
        """Update retry information"""
        try:
            self.retry_count = attempt
            self.last_retry_time = datetime.now(timezone.utc)
            self.status = 'running'
        except Exception as e:
            logger.error(f"Failed to update retry info for execution record {self.id}: {e}")
            raise