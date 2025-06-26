"""
Execution Record Service - Handles all execution record operations
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from database import get_db
from models.execution_record import ExecutionRecord

# Setup logging
from worker.config.logging_config import setup_logging
logger = setup_logging(__name__)

class ExecutionRecordService:
    """Service for managing execution records in the database"""
    
    def __init__(self):
        pass
    
    def create_execution_record(self, spreadsheet_id: str, execution_time: datetime) -> ExecutionRecord:
        """
        Create a new execution record in the database
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            execution_time: When the execution started
            
        Returns:
            ExecutionRecord: New execution record
        """
        db = next(get_db())
        try:
            # Generate worker ID (you might want to make this configurable)
            worker_id = f"worker_{os.getpid()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create new execution record
            execution_record = ExecutionRecord(
                execution_time=execution_time,
                worker_id=worker_id,
                data_hash=None,  # Will be set when data is loaded
                spreadsheet_id=spreadsheet_id,
                status='running',   
            )
            
            # Add to database session
            db.add(execution_record)
            db.commit()
            db.refresh(execution_record)
            
            logger.info(f"Created execution record for {spreadsheet_id}")
            return execution_record
            
        except Exception as e:
            logger.error(f"Failed to create execution record for {spreadsheet_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def save_execution_record(self, execution_record: ExecutionRecord):
        """
        Save the execution record to the database
        
        Args:
            execution_record: Execution record to save
        """
        if execution_record is None:
            logger.warning("Attempted to save None execution record")
            return
            
        logger.info(f"Saving execution record for {execution_record.spreadsheet_id} with status {execution_record.status}")
        db = next(get_db())
        try:
            # Update the record in the database
            db.merge(execution_record)
            db.commit()
            
            logger.info(f"Saved execution record for {execution_record.spreadsheet_id} with status {execution_record.status}")
            
        except Exception as e:
            logger.error(f"Failed to save execution record for {execution_record.spreadsheet_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def load_execution_record(self, spreadsheet_id: str, condition_map: Dict[str, Any]) -> Optional[ExecutionRecord]:
        """
        Load the latest execution record for a spreadsheet from the database
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            
        Returns:
            ExecutionRecord: Latest execution record or None if not found
        """
        db = next(get_db())
        try:
            # Start with base query
            query = db.query(ExecutionRecord).filter_by(spreadsheet_id=spreadsheet_id)
            
            # Apply additional conditions if provided
            if condition_map:
                for key, value in condition_map.items():
                    if hasattr(ExecutionRecord, key):
                        query = query.filter(getattr(ExecutionRecord, key) == value)
            
            # Get the most recent record matching conditions
            record = query.order_by(ExecutionRecord.execution_time.desc()).first()
            
            if record:
                logger.info(f"Loaded execution record for {spreadsheet_id} from {record.execution_time}, with status {record.status}")
            else:
                logger.info(f"No execution record found for {spreadsheet_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Failed to load execution record for {spreadsheet_id}: {e}")
            return None
        finally:
            db.close()
    
    def load_execution_record_by_id(self, record_id: int) -> Optional[ExecutionRecord]:
        """
        Load execution record by primary key
        
        Args:
            record_id: Primary key of the execution record
            
        Returns:
            ExecutionRecord: The specific execution record
        """
        db = next(get_db())
        try:
            record = db.query(ExecutionRecord).get(record_id)  # ✅ Uses primary key lookup
            if record:
                logger.debug(f"Loaded execution record {record_id} for {record.spreadsheet_id}")
            return record
            
        except Exception as e:
            logger.error(f"Failed to load execution record {record_id}: {e}")
            return None
        finally:
            db.close()
    
    def get_data_hash(self, data) -> str:
        """
        Generate a hash of the data to detect changes
        
        Args:
            data: DataFrame to hash
            
        Returns:
            str: Hash of the data
        """
        # Use the ExecutionRecord's generate_data_hash method
        return ExecutionRecord.generate_data_hash(data)
    
    def data_has_changed(self, spreadsheet_id: str, current_data) -> bool:
        """
        Check if the data has changed since last successful execution using database records
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            current_data: Current raw data
            
        Returns:
            bool: True if data has changed, False otherwise
        """
        current_hash = self.get_data_hash(current_data)
        
        # Get the latest execution record from database
        record = self.load_execution_record(spreadsheet_id, {'status': 'completed'})
        
        if not record:
            logger.info(f"No previous completedexecution record found for {spreadsheet_id}, will process")
            return True
        
        last_hash = record.data_hash
        # If last_hash is None, it means the previous execution didn't complete properly
        if last_hash is None:
            logger.info(f"Previous execution record for {spreadsheet_id} has no data_hash, will process")
            return True
            
        if last_hash != current_hash:
            logger.info(f"Data has changed for {spreadsheet_id} (hash: {current_hash[:8]}... vs {last_hash[:8]}...)")
            return True
        elif record.status == 'completed':
            logger.info(f"Data unchanged for {spreadsheet_id}, skipping processing")
            return False
        else:
            logger.info(f"Last execution had failed with status {record.status} for {spreadsheet_id}, will process")
            return True
    
    def update_execution_record_data_hash(self, execution_record: ExecutionRecord, data):
        """
        Update the execution record with the data hash
        
        Args:
            execution_record: Execution record to update
            data: Data to generate hash from
        """
        if execution_record is None:
            logger.warning("Attempted to update data hash for None execution record")
            return
            
        db = next(get_db())
        try:
            execution_record.data_hash = self.get_data_hash(data)
            db.merge(execution_record)
            db.commit()
            logger.debug(f"Updated data hash for execution record {execution_record.id}")
        except Exception as e:
            logger.error(f"Failed to update data hash: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def get_execution_history(self, spreadsheet_id: str, limit: int = 10) -> List[Dict]:
        """
        Get execution history for a spreadsheet
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: List of execution records as dictionaries
        """
        db = next(get_db())
        try:
            records = db.query(ExecutionRecord).filter_by(
                spreadsheet_id=spreadsheet_id
            ).order_by(ExecutionRecord.execution_time.desc()).limit(limit).all()
            
            return [record.to_dict() for record in records]
            
        except Exception as e:
            logger.error(f"Failed to get execution history for {spreadsheet_id}: {e}")
            return []
        finally:
            db.close()
    
    def get_execution_statistics(self, spreadsheet_id: str = None) -> Dict:
        """
        Get execution statistics
        
        Args:
            spreadsheet_id: Optional spreadsheet ID to filter by
            
        Returns:
            Dict: Execution statistics
        """
        db = next(get_db())
        try:
            query = db.query(ExecutionRecord)
            
            if spreadsheet_id:
                query = query.filter_by(spreadsheet_id=spreadsheet_id)
            
            total_executions = query.count()
            successful_executions = query.filter_by(status='completed').count()
            failed_executions = query.filter_by(status='failed').count()
            
            # Get average processing duration
            avg_duration = db.query(db.func.avg(ExecutionRecord.processing_duration)).scalar() or 0
            
            # Get total rows processed
            total_rows = db.query(db.func.sum(ExecutionRecord.rows_processed)).scalar() or 0
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'average_duration': avg_duration,
                'total_rows_processed': total_rows
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution statistics: {e}")
            return {}
        finally:
            db.close() 