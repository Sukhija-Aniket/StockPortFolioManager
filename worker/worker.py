import pika
import json
import asyncio
import aiofiles
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import os
import sys

# Setup logging
from utils.logging_config import setup_logging
logger = setup_logging(__name__)

# Import configuration and shared library
from config import Config
from stock_portfolio_shared.utils.common import CommonUtils

# Import the trading service
from services.trading_service import TradingService

# Initialize configuration and shared utilities
config = Config()
common_utils = CommonUtils()

class AsyncWorker:
    """Async worker for processing spreadsheet tasks"""
    
    def __init__(self):
        # Get configuration from environment variables
        self.max_workers = int(os.getenv('WORKER_CONCURRENCY', 4))
        self.task_timeout = int(os.getenv('WORKER_TIMEOUT', 300))
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.running_tasks = {}
        
        # Initialize the trading service
        self.trading_service = TradingService(max_workers=self.max_workers)
        
        logger.info(f"Initialized AsyncWorker with {self.max_workers} workers and {self.task_timeout}s timeout")
    
    async def process_spreadsheet_async(self, spreadsheet, credentials):
        """Process a single spreadsheet asynchronously"""
        try:
            logger.info(f"Starting async processing for spreadsheet: {spreadsheet['title']}")
            
            # Extract spreadsheet ID from URL using shared library
            spreadsheet_id = common_utils.extract_spreadsheet_id(spreadsheet['url'])
            if not spreadsheet_id:
                logger.error(f"Invalid spreadsheet URL: {spreadsheet['url']}")
                return False
            
            # Use the trading service to process the spreadsheet
            result = await self.trading_service.process_spreadsheet_async(
                spreadsheet_id, 
                credentials, 
                'sheets'
            )
            
            logger.info(f"Completed async processing for {spreadsheet['title']}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Exception in async processing for {spreadsheet['title']}: {e}")
            return False
    
    async def process_batch_async(self, spreadsheets, credentials):
        """Process multiple spreadsheets concurrently"""
        try:
            logger.info(f"Starting batch processing for {len(spreadsheets)} spreadsheets")
            
            # Use the trading service's batch processing method
            success_count = await self.trading_service.process_batch_async(spreadsheets, credentials)
            
            logger.info(f"Batch processing completed: {success_count}/{len(spreadsheets)} successful")
            return success_count
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return 0
    
    def shutdown(self):
        """Clean shutdown of the worker"""
        logger.info("Shutting down AsyncWorker")
        self.trading_service.shutdown()
        self.executor.shutdown(wait=True)
        logger.info("AsyncWorker shutdown complete")

async def async_callback(ch, method, properties, body, worker):
    """Async RabbitMQ message callback"""
    try:
        data = json.loads(body)
        logger.info(f"Received message with {len(data.get('spreadsheets', []))} spreadsheets")
        
        spreadsheets = data.get('spreadsheets', [])
        credentials = data.get('credentials')
        
        if not spreadsheets:
            logger.warning("No spreadsheets provided in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        if not credentials:
            logger.error("No credentials provided in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        # Process spreadsheets asynchronously
        success_count = await worker.process_batch_async(spreadsheets, credentials)
        
        logger.info(f"Processed {success_count}/{len(spreadsheets)} spreadsheets successfully")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error in async callback: {e}")
        # Reject message and requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def sync_callback(ch, method, properties, body, worker):
    """Synchronous callback wrapper for RabbitMQ"""
    asyncio.run(async_callback(ch, method, properties, body, worker))

def main():
    """Main function to start the async worker"""
    worker = None
    connection = None
    
    try:
        logger.info("Initializing async worker script")
        
        # Initialize the worker
        worker = AsyncWorker()
        
        # Create RabbitMQ connection
        credentials_rabbitmq = pika.PlainCredentials(
            config.RABBITMQ_USERNAME, 
            config.RABBITMQ_PASSWORD
        )
        
        logger.info(f"Connecting to RabbitMQ at {config.RABBITMQ_HOST}")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
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