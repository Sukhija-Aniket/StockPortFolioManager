import pika
import json
import subprocess, os, sys

scripts_directory = os.path.dirname(__file__)
parent_directory = os.path.dirname(scripts_directory)
sys.path.append(parent_directory)


def callback(ch, method, properties, body):
    data = json.loads(body)
    print('Received data:', data)
    # ch.basic_ack(delivery_tag=method.delivery_tag)
    # return
    spreadsheets = data['spreadsheets']
    credentials = data['credentials']
    print("Processing spreadsheets:", spreadsheets)
    # Add your heavy task processing code here
    
    for spreadsheet in spreadsheets:
        print("updating spreadsheet: ", spreadsheet)
        #  Run the add_data.py script with the file path and spreadsheet_id as arguments
        process = subprocess.Popen(['python3.8', os.path.join(os.path.abspath(scripts_directory), "tradingScript.py"), 'None', 'sheets', spreadsheet['url'].split('/d/')[1], json.dumps(credentials)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error updating sheet {spreadsheet['title']}: {stderr.decode()}")
        else:
            print(f"Successfully processed {spreadsheet['title']}: {stdout.decode()}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()