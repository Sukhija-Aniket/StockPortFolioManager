from extensions import db
from datetime import datetime
import hashlib
import logging

class ExecutionRecord(db.Model):
    """Model for storing worker execution records"""
    __tablename__ = 'execution_records'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Core tracking fields
    execution_time = db.Column(db.DateTime, nullable=False)
    worker_id = db.Column(db.String(100), nullable=False, index=True)
    data_hash = db.Column(db.String(64), nullable=False, index=True)
    spreadsheet_id = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.String(120), index=True)
    
    # Additional useful fields
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, running, completed, failed
    processing_duration = db.Column(db.Float)  # seconds
    rows_processed = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    # Metadata fields
    created_at = db.Column(db.DateTime, default=datetime.now(datetime.UTC))
    updated_at = db.Column(db.DateTime, default=datetime.now(datetime.UTC), onupdate=datetime.now(datetime.UTC))
    
    # Performance metrics
    memory_usage = db.Column(db.Float)  # MB
    cpu_usage = db.Column(db.Float)  # percentage
    
    # Retry information
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    last_retry_time = db.Column(db.DateTime)
    
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
            'user_id': self.user_id,
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
            self.last_retry_time = datetime.now(datetime.UTC)
            self.status = 'running'
            # updated_at will be automatically updated by SQLAlchemy onupdate
        except Exception as e:
            # Log the error but don't raise to prevent cascading failures
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update retry info for execution record {self.id}: {e}")
            # Re-raise to let caller handle it
            raise