import logging
import pika
import json

from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType
from config import Config
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
import os
import pandas as pd
from stock_portfolio_shared.utils.data_processor import DataProcessor
logger = logging.getLogger(__name__)

class DataService:
    """Service class for handling data processing and upload operations"""
    
    def __init__(self):
        self.sheets_manager = SheetsManager()
        self.excel_manager = ExcelManager()
        self.rabbitmq_config = {
            'host': Config.RABBITMQ_HOST,
            'username': Config.RABBITMQ_USERNAME,
            'password': Config.RABBITMQ_PASSWORD
        }
    
    def send_to_worker(self, tasks, credentials):
        """Send data processing task to worker via RabbitMQ"""
        try:
            # Create connection to RabbitMQ
            credentials_rabbitmq = pika.PlainCredentials(
                self.rabbitmq_config['username'],
                self.rabbitmq_config['password']
            )
            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_config['host'],
                    credentials=credentials_rabbitmq
                )
            )
            
            channel = connection.channel()
            channel.queue_declare(queue='task_queue', durable=True)
            
            # Prepare message
            message = {
                'tasks': [task.to_dict() for task in tasks],
                'credentials': credentials
            }
            
            # Send message
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                )
            )
            
            connection.close()
            logger.info(f"Sent task to worker for {len(tasks)} spreadsheets")
            return True
            
        except Exception as e:
            logger.error(f"Error sending task to worker: {e}")
            raise
    
    def process_data_upload(self, file_path, spreadsheet_task: SpreadsheetTask):
        """Process data upload using the shared library"""
        manager = self.sheets_manager if spreadsheet_task.spreadsheet_type == SpreadsheetType.SHEETS else self.excel_manager
        try:
            sheet_names = manager.get_sheet_names(spreadsheet_task)
            # Time to obtain input data
            if file_path is not None and os.path.exists(file_path):
                # Handling User data and preparing raw data
                logger.info(f"Processing file: {file_path}")
                input_data = pd.read_csv(file_path)
                # Use shared library's data processor for formatting
                final_input_data = DataProcessor.format_add_data(input_data)
                spreadsheet = manager.get_spreadsheet(spreadsheet_task)
                return manager.add_data(final_input_data, spreadsheet, sheet_names[0])
        except Exception as e:
            logger.error(f"Error processing data upload: {e}")
            raise
    
    def validate_file_upload(self, file):
        """Validate uploaded file"""
        try:
            if not file:
                raise ValueError("No file provided")
            
            # Check file size
            if file.content_length and file.content_length > Config.MAX_CONTENT_LENGTH:
                raise ValueError("File too large")
            
            # Check file extension
            allowed_extensions = {'.csv', '.xlsx', '.xls'}
            if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise ValueError("Invalid file type. Only CSV and Excel files are allowed")
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise 