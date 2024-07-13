from flask import Flask, redirect, url_for, session, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os, sys
import json
from datetime import datetime
from database import configure_db, User, Spreadsheet
from flask_cors import CORS
import subprocess

parent_directory = os.path.dirname(os.path.dirname(__file__))
scripts_directory = os.path.join(parent_directory, 'scripts')
sys.path.append(parent_directory)

from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('APP_SECRET_KEY')
db = configure_db(app)
PORT=os.getenv('PORT')

# Path to your Google Sheets API credentials

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # allows to use http otherwise https is required
credentials_file = os.path.join(parent_directory, 'secrets', 'credentials.json')
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
    redirect_uri="http://localhost:5000/oauth2callback"
)


@app.get('/user_data')
def get_user_data():
    user = session.get('user')
    print("but here")
    if not user:
        print("not coming here")
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(user)

@app.get('/logout')
def logout():
    session.clear()
    return redirect('http://localhost:3000/')

@app.get('/spreadsheets')
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


@app.route('/authorize')
def authorize():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback') # by mistake it is callbak and not callback
def oauth2callback():
    
    flow.fetch_token(authorization_response=request.url)
    
    if not session['state'] == request.args['state']:
        return redirect("http://localhost:3000/")

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    service = build('oauth2', 'v2', credentials=credentials)
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
    
    return redirect('http://localhost:3000/')

@app.post('/add_data')
def add_data():
    url = request.form.get('spreadsheeturl')
    files = request.files.getlist('files')
    
    messages = {}
    for file in files:
        file_path = os.path.join(parent_directory, f'temp/{file.filename}')
        file.save(file_path)
        # Run the add_data.py script with the file path and spreadsheet_id as arguments
        process = subprocess.Popen(['python', os.path.join(os.path.abspath(scripts_directory), "addData.py"), os.path.abspath(file_path), 'sheets', url.split('/d/')[1], json.dumps(session.get('credentials'))],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f"Error processing file {file.filename}: {stderr.decode()}")
            messages[file.filename] = "Error processing file"
        else:
            messages[file.filename] = "Successfully Processed"
            print(f'Successfully processed {file.filename}: {stdout.decode()}')
    
    return jsonify({"message": messages}), 200

@app.post('/create_spreadsheet') # this is a post request with title
def create_spreadsheet():
    print(session)
    user = session.get('user')
    print("coming here")
    print(user)
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
    service = build('sheets', 'v4', credentials=credentials_obj)
    drive_service = build('drive', 'v3', credentials=credentials_obj)

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

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run('localhost', port=int(PORT), debug=True)
