from flask import redirect, session, request, jsonify, Blueprint
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json
from datetime import datetime
import subprocess
import pika
import pika.delivery_mode
from addData import upload_data
from googleapiclient.errors import HttpError
import google_auth_httplib2
import httplib2
import certifi
http = httplib2.Http(ca_certs=certifi.where(), disable_ssl_certificate_validation=True)

app_directory = os.path.dirname(__file__)
scripts_directory = os.path.join(os.path.dirname(app_directory), 'scripts')

from dotenv import load_dotenv
env_file = os.path.join(app_directory, 'secrets', '.env')
load_dotenv(env_file)

from database import db, User, Spreadsheet
from utils import credentials_to_dict

# Path to your Google Sheets API credentials

credentials_file = os.path.join(app_directory, 'secrets', 'credentials.json')
scopes = [
    "openid",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/userinfo.profile"   
]

# OAuth 2.0 setup
flow = Flow.from_client_secrets_file(
    credentials_file,
    scopes = scopes,
    redirect_uri=f"http://{os.getenv('BACKEND_SERVICE')}/oauth2callback"
)
  

main_bp = Blueprint('main', __name__)

# Authorization Related Stuff
@main_bp.route('/authorize')
def authorize():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@main_bp.route('/oauth2callback') # by mistake it is callbak and not callback
def oauth2callback():
    
    flow.fetch_token(authorization_response=request.url)
    
    if not session['state'] == request.args['state']:
        return redirect(f"http://{os.getenv('FRONTEND_SERVICE')}/")
        

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    authorized_http = google_auth_httplib2.AuthorizedHttp(credentials, http=http)
    service = build('oauth2', 'v2', http=authorized_http)
    profile = service.userinfo().get().execute()
    
    email = profile['email']
    google_id = profile['id']
    name = profile['name']
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(email=email, name=name, google_id=google_id)
        db.session.add(user)
        db.session.commit()
        
    # Storing user information in session for login persistence
    session['user'] = {'name': user.name, 'email': user.email, 'google_id': user.google_id, 'id': user.id}
    
    return redirect(f"http://{os.getenv('FRONTEND_SERVICE')}/")

@main_bp.get('/user_data')
def get_user_data():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(user)

@main_bp.get('/logout')
def logout():
    session.clear()
    return redirect(f"http://{os.getenv('FRONTEND_SERVICE')}/")

# Spreadsheet Related Routes
@main_bp.get('/spreadsheets')
def get_spreadsheets():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Here, there is no need for me to have a user_record, as user contains all the required information.
    user_record = User.query.filter_by(email=user['email']).first()
    if user_record:
        spreadsheets = Spreadsheet.query.filter_by(user_id=user_record.id).all()
        spreadsheets_data = [
            {
                'title': sheet.title,
                'url': f'https://docs.google.com/spreadsheets/d/{sheet.spreadsheet_id}',
                'date_created': sheet.date_created
            }
            for sheet in spreadsheets
        ]
        return jsonify(spreadsheets_data)
    else:
        return jsonify({'error': 'User not found'}), 404
    
    
# State or Data Modifying Functions
@main_bp.post('/create_spreadsheet') # this is a post request with title
def create_spreadsheet():
    user = session.get('user')
    print(f"Session: {session} and user: {user}")
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_record = User.query.filter_by(email=user['email']).first()
    if not user_record:
        return jsonify({'error': 'User not found'}), 404
    
    user_email = session.get('user_email')
    data = request.get_json()
    title = data.get('title')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    credentials = session['credentials']
    credentials_obj = Credentials(**credentials)
    authorized_http = google_auth_httplib2.AuthorizedHttp(credentials_obj, http=http)
    service = build('sheets', 'v4', http=authorized_http)
    drive_service = build('drive', 'v3', http=authorized_http)

    spreadsheet = {
        'properties': {
            'title': title
        }
    }

    sheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = sheet.get('spreadsheetId')
    
    requests = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": 0,
                    "title": "Transactions"
                },
                "fields": "title"
            }
        }
    ]
    titles = ["TransDetails Sorted", "Share Profit/Loss", "Daily Profit/Loss", "Taxation"]
    for i in range(4):
        requests.append({
            "addSheet": {
                "properties": {
                    "title": titles[i]
                }
            }       
        })
    
    body = {
        "requests":requests
    }
    
    # Executing Batch Update
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    # Adding the spreadsheet to the database
    spreadsheet_db = Spreadsheet(title=title, user_id=user['id'], date_created=datetime.now().date(), spreadsheet_id=spreadsheet_id)
    db.session.add(spreadsheet_db)
    db.session.commit()

    if user_email:
        
    # Share the spreadsheet with the user
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': user_email
        }
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            fields='id',
        ).execute()

    return jsonify({"message": "spreadsheet created successfully", "spreadsheet_id": spreadsheet_id}), 200

@main_bp.post('/remove_spreadsheet')  # This is a post request with spreadsheet_id
def remove_spreadsheet():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    print("this is the data", data)
    spreadsheet_url = data.get('spreadsheet_url')
    print("here is the spreadsheet url", spreadsheet_url)
    spreadsheet_id = spreadsheet_url.split('/d/')[1]
    print("here is the spreadsheet id", spreadsheet_id)
    
    print("This is working as the request reaches here")
    
    if not spreadsheet_id:
        return jsonify({'error': 'Spreadsheet ID is required'}), 400
    
    print("This is working as the request reaches here")
    # Fetch the spreadsheet record from the database
    spreadsheet_record = Spreadsheet.query.filter_by(spreadsheet_id=spreadsheet_id, user_id=user['id']).first()
    if not spreadsheet_record:
        return jsonify({'error': 'Spreadsheet not found'}), 404
    
    credentials = session['credentials']
    credentials_obj = Credentials(**credentials)
    authorized_http = google_auth_httplib2.AuthorizedHttp(credentials_obj, http=http)
    drive_service = build('drive', 'v3', http=authorized_http)
    
    print("About to delete the spreadsheet record")
    try:
        # Remove the spreadsheet from Google Drive
        drive_service.files().delete(fileId=spreadsheet_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            print("Could not delete the spreadsheet as it doesn't exist")
        else:
            print(f"Error removing spreadsheet: {e}")
            return jsonify({'error': 'Failed to remove spreadsheet'}), 500
    except FileNotFoundError as e:
        print("Could not delete the spreadsheet as it doesn't exist")
    except Exception as e:
        print(f"Error removing spreadsheet: {e}")
        return jsonify({'error': 'Failed to remove spreadsheet'}), 500
    try:
        # Remove the spreadsheet record from the database
        db.session.delete(spreadsheet_record)
        db.session.commit()
        
        return jsonify({"message": "Spreadsheet removed successfully"}), 200
    except Exception as e:
        print(f"Error removing spreadsheet: {e}")
        return jsonify({'error': 'Failed to remove spreadsheet'}), 500


@main_bp.post('/add_data')
def add_data():
    print("here it comes")
    url = request.form.get('spreadsheeturl')
    files = request.files.getlist('files')
    google_id = session.get('user')['google_id']
    print('HERE IT DOES NOT COME')
    messages = {}
    for file in files:
        if not os.path.exists(os.path.join(app_directory, 'temp')):
            os.makedirs(os.path.join(app_directory, 'temp'))
        file_path = os.path.join(app_directory, f'temp/{file.filename}_{google_id}')
        file.save(file_path)
        # Run the add_data.py script with the file path and spreadsheet_id as arguments
        upload_data(os.path.abspath(file_path), 'sheets', url.split('/d/')[1], session.get('credentials'), http)
    
    return jsonify({"message": messages}), 200

@main_bp.post('/sync_data')
def sync_data():
    data = request.get_json()
    spreadsheets = json.loads(data.get('spreadsheets'))
    print("Syncing Data for spreadsheetID: ", spreadsheets)
    
    credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USERNAME'), os.getenv('RABBITMQ_PASSWORD'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv("RABBITMQ_HOST"), credentials=credentials))
    channel = connection.channel()
    print("Connection has been established to channel: ", channel)
    channel.queue_declare(queue='task_queue', durable=True)
    
    message = json.dumps({
        'spreadsheets': spreadsheets,
        'credentials': session.get('credentials')
        })
    print("Publishing message to RabbitMQ: ", message)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=pika.DeliveryMode.Persistent,  # make message persistent
        ))
    print("Message published successfully")
    
    connection.close()
    return jsonify({"message": "Data queued successfully"}), 200

def initialize_routes(app):
    app.register_blueprint(main_bp)