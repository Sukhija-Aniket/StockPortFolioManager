import asyncio
import pika
import json
import os
from config import Config
from database import init_db, test_connection
from services.trading_orchestrator import TradingOrchestrator
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType
from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from stock_portfolio_shared.utils.excel_manager import ExcelManager
from concurrent.futures import ThreadPoolExecutor


sheets_manager = SheetsManager()
excel_manager = ExcelManager()

# Setup logging
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

class AsyncWorker:
    """Async worker for processing spreadsheet tasks"""
    
    def __init__(self):
        # Get configuration from environment variables
        self.max_workers = int(os.getenv('WORKER_CONCURRENCY', 4))
        self.task_timeout = int(os.getenv('WORKER_TIMEOUT', 300))
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.sheets_orchestrator = TradingOrchestrator(sheets_manager, self.executor)
        self.excel_orchestrator = TradingOrchestrator(excel_manager, self.executor)
        
        logger.info(f"Initialized AsyncWorker with {self.max_workers} workers and {self.task_timeout}s timeout")
    
    async def process_spreadsheet_async(self, task: SpreadsheetTask):
        """Process a single spreadsheet asynchronously"""
        try:
            logger.info(f"Starting async processing for spreadsheet: {task.spreadsheet_id}")
            
            # Process the spreadsheet
            if task.spreadsheet_type == SpreadsheetType.SHEETS:
                result = await self.sheets_orchestrator.process_spreadsheet(task)
            elif task.spreadsheet_type == SpreadsheetType.EXCEL:
                result = await self.excel_orchestrator.process_spreadsheet(task)
            else:
                raise ValueError(f"Unsupported task type: {task.spreadsheet_type}")
            
            logger.info(f"Completed async processing for {task.spreadsheet_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Exception in async processing for {task.spreadsheet_id}: {e}")
            return False
    
    async def process_batch_async(self, tasks):
        """Process multiple spreadsheets concurrently"""
        try:
            logger.info(f"Starting batch processing for {len(tasks)} tasks")
            
            # Process tasks concurrently
            tasks_list = [self.process_spreadsheet_async(task) for task in tasks]
            results = await asyncio.gather(*tasks_list, return_exceptions=True)
            
            # Count successful results
            success_count = sum(1 for result in results if result is True)
            
            logger.info(f"Batch processing completed: {success_count}/{len(tasks)} successful")
            return success_count
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return 0
    
    def shutdown(self):
        """Clean shutdown of the worker"""
        logger.info("Shutting down AsyncWorker")
        self.executor.shutdown(wait=True)
        logger.info("AsyncWorker shutdown complete")

async def async_callback(ch, method, properties, body, worker: AsyncWorker):
    """Async RabbitMQ message callback"""
    try:
        data = json.loads(body)
        logger.info(f"Received message with {len(data.get('tasks', []))} tasks")
        
        tasks_data = data.get('tasks', [])
        tasks = [SpreadsheetTask.from_dict(task) for task in tasks_data]
        
        if not tasks:
            logger.warning("No tasks provided in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Process tasks asynchronously
        success_count = await worker.process_batch_async(tasks)
        
        logger.info(f"Processed {success_count}/{len(tasks)} tasks successfully")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error in async callback: {e}")
        # Reject message and requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def sync_callback(ch, method, properties, body, worker: AsyncWorker):
    """Synchronous callback wrapper for RabbitMQ"""
    asyncio.run(async_callback(ch, method, properties, body, worker))

def main():
    """Main function to start the async worker"""
    worker = None
    connection = None
    
    try:
        logger.info("Initializing async worker script")
        
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Test database connection
        if not test_connection():
            logger.error("Database connection failed")
            return
        
        # Initialize database tables
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize the worker
        worker = AsyncWorker()
        
        # Create RabbitMQ connection
        credentials_rabbitmq = pika.PlainCredentials(
            Config.RABBITMQ_USERNAME, 
            Config.RABBITMQ_PASSWORD
        )
        
        logger.info(f"Connecting to RabbitMQ at {Config.RABBITMQ_HOST}")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                credentials=credentials_rabbitmq
            )
        )
        
        channel = connection.channel()
        
        # Declare queue
        channel.queue_declare(queue='task_queue', durable=True)
        channel.basic_qos(prefetch_count=1)
        
        # Set up consumer with async callback
        channel.basic_consume(
            queue='task_queue', 
            on_message_callback=lambda ch, method, properties, body: sync_callback(ch, method, properties, body, worker)
        )
        
        logger.info('Async worker started. Waiting for messages. To exit press CTRL+C')
        
        # Start consuming messages
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Async worker stopped by user")
    except Exception as e:
        logger.error(f"Error in async worker: {e}")
        raise
    finally:
        # Clean shutdown
        if worker:
            worker.shutdown()
        if connection and connection.is_open:
            connection.close()
            logger.info("RabbitMQ connection closed")

if __name__ == "__main__":
    main()