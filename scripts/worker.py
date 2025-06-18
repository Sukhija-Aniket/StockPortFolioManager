import pika
import json
import subprocess, os, sys
import logging

# Setup logging
from logging_config import setup_logging
logger = setup_logging()

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)

from dotenv import load_dotenv
env_file = os.path.join(scripts_directory, 'secrets', '.env')
load_dotenv(env_file)

logger.info("Worker script initialized")

def callback(ch, method, properties, body):
    data = json.loads(body)
    logger.info("Received message type: %s, spreadsheets: %s", type(data['spreadsheets']), data['spreadsheets'])
    spreadsheets = data['spreadsheets']
    credentials = data['credentials']
    logger.info("Processing spreadsheets: %s", spreadsheets)
    # Add your heavy task processing code here
    
    for spreadsheet in spreadsheets:
        logger.info("updating spreadsheet: %s", spreadsheet)
        #  Run the add_data.py script with the file path and spreadsheet_id as arguments
        process = subprocess.Popen(['python3.8', os.path.join(os.path.abspath(scripts_directory), "tradingScript.py"), 'None', 'sheets', spreadsheet['url'].split('/d/')[1], json.dumps(credentials)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error("Error updating sheet: %s: %s", spreadsheet['title'], stdout.decode())
            logger.error("Error updating sheet %s: %s", spreadsheet['title'], stderr.decode())
        else:
            logger.info("Successfully processed %s: %s", spreadsheet['title'], stdout.decode())
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USERNAME'), os.getenv('RABBITMQ_PASSWORD'))
logger.info("Connecting to RabbitMQ, credentials=%s, host=%s", credentials, os.getenv('RABBITMQ_HOST'))
connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"), credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)

logger.info('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()