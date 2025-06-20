from flask import Blueprint, request, jsonify, session
from services.data_service import DataService
from services.spreadsheet_service import SpreadsheetService
from services.google_service import GoogleService
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

data_bp = Blueprint('data', __name__, url_prefix='/data')
data_service = DataService()
spreadsheet_service = SpreadsheetService()
google_service = GoogleService()

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        credentials = session.get('credentials')
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        if not credentials:
            return jsonify({'error': 'No credentials found'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@data_bp.route('/upload', methods=['POST'])
@require_auth
def upload_data():
    """Upload and process data file"""
    try:
        user = session.get('user')
        credentials = session.get('credentials')
        
        # Check if file was uploaded
        # TODO:Improve later for multiple files.
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Validate file
        data_service.validate_file_upload(file)
        
        # Get spreadsheet ID from form data
        spreadsheet_id = request.form.get('spreadsheet_id')
        if not spreadsheet_id:
            return jsonify({'error': 'Spreadsheet ID is required'}), 400
        
        # Verify spreadsheet ownership
        spreadsheet = spreadsheet_service.get_spreadsheet_by_id(spreadsheet_id, user['id'])
        if not spreadsheet:
            return jsonify({'error': 'Spreadsheet not found or access denied'}), 404
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            data_service.process_data_upload(
                temp_file_path, 
                spreadsheet_id, 
                credentials
            )
            
            return jsonify({'message': 'Data uploaded successfully'})
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading data: {e}")
        return jsonify({'error': 'Failed to upload data'}), 500

@data_bp.route('/sync', methods=['POST'])
@require_auth
def sync_data():
    """Sync data across multiple spreadsheets"""
    try:
        user = session.get('user')
        credentials = session.get('credentials')
        
        data = request.get_json()
        logger.info("this is the data", data)
        spreadsheets = data.get('spreadsheets', [])
        
        if not spreadsheets:
            return jsonify({'error': 'No spreadsheets provided'}), 400
        # Verify all spreadsheets belong to user
        for spreadsheet_data in spreadsheets:
            logger.info("this is the spreadsheet data", spreadsheet_data)
            spreadsheet_id = spreadsheet_data.get('url', '').split('/d/')[1] if '/d/' in spreadsheet_data.get('url', '') else None
            if not spreadsheet_id:
                return jsonify({'error': 'Invalid spreadsheet URL'}), 400
            spreadsheet = spreadsheet_service.get_spreadsheet_by_id(spreadsheet_id, user['id'])
            if not spreadsheet:
                return jsonify({'error': f'Spreadsheet {spreadsheet_data.get("title")} not found or access denied'}), 404
        # Send task to worker
        data_service.send_to_worker(spreadsheets, credentials)
        return jsonify({'message': 'Sync task queued successfully'})
        
    except Exception as e:
        logger.error(f"Error syncing data: {e}")
        return jsonify({'error': 'Failed to sync data'}), 500 