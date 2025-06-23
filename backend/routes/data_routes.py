from flask import Blueprint, request, jsonify, session
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType
from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
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


def _get_spreadsheet_id(spreadsheet_url):
    """
    Get spreadsheet ID from URL
    """
    return spreadsheet_url.split('/d/')[1].split('/')[0]

def _spreadsheet_to_task(spreadsheet_data, credentials):
    """
    Convert spreadsheet data to SpreadsheetTask object
    
    Args:
        spreadsheet_data (dict): Spreadsheet data containing url, title, etc.
        credentials (dict): Google credentials for API access
    
    Returns:
        SpreadsheetTask: Task object for processing
        
    Raises:
        ValueError: If required data is missing or invalid
    """
    
    # Extract spreadsheet ID from URL
    url = spreadsheet_data.get('url', '')
    spreadsheet_id = None
    
    if not url:
        raise ValueError("Spreadsheet URL is required")
    
   
    try:
        spreadsheet_id = _get_spreadsheet_id(url)
    except Exception as e:
        raise ValueError(f"Invalid spreadsheet URL format: {url}, exception: {e}")
    
    # Extract title with fallback
    title = spreadsheet_data.get('title')
    if not title:
        title = f"Spreadsheet-{spreadsheet_id[:8]}"  # Fallback title
    
    # Create SpreadsheetTask
    task = SpreadsheetTask(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_type=SpreadsheetType.SHEETS,
        credentials=credentials,
        title=title
    )
    
    return task

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

@data_bp.route('/add', methods=['POST'])
@require_auth
def add_data():
    """Add data to spreadsheet"""
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
        spreadsheet_url = request.form.get('spreadsheet_url')
        spreadsheet_id = _get_spreadsheet_id(spreadsheet_url)
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
        
        # Create spreadsheet data for task conversion
        spreadsheet_data = {
            'url': spreadsheet_url,
            'title': request.form.get('title') or spreadsheet.title
        }
        
        # Use the utility function to create task
        try:
            spreadsheet_task = _spreadsheet_to_task(spreadsheet_data, credentials)
        except ValueError as e:
            return jsonify({'error': f'Invalid spreadsheet data: {e}'}), 400
        except Exception as e:
            logger.error(f"Error creating spreadsheet task: {e}")
            return jsonify({'error': 'Failed to create task'}), 500
        
        try:
            data_service.process_data_upload(
                temp_file_path, 
                spreadsheet_task
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
            
        # Use the utility function to convert spreadsheets to tasks
        tasks = []
        errors = []
        
        for i, spreadsheet_data in enumerate(spreadsheets):
            try:
                task = _spreadsheet_to_task(spreadsheet_data, credentials)
                tasks.append(task)
            except ValueError as e:
                error_msg = f"Error converting spreadsheet {i}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error converting spreadsheet {i}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if not tasks:
            return jsonify({'error': 'No valid tasks created', 'details': errors}), 400
        
        if errors:
            logger.warning(f"Some spreadsheets had issues: {errors}")
        
        # Verify all spreadsheets belong to user
        for spreadsheet_data in spreadsheets:
            logger.info("this is the spreadsheet data", spreadsheet_data)
            spreadsheet_id = _get_spreadsheet_id(spreadsheet_data.get('url'))  
            if not spreadsheet_id:
                return jsonify({'error': 'Invalid spreadsheet URL'}), 400
            spreadsheet = spreadsheet_service.get_spreadsheet_by_id(spreadsheet_id, user['id'])
            if not spreadsheet:
                return jsonify({'error': f'Spreadsheet {spreadsheet_data.get("title")} not found or access denied'}), 404
        
        # Send tasks to worker instead of spreadsheets
        data_service.send_to_worker(tasks, credentials)
        return jsonify({
            'message': f'Sync task queued successfully for {len(tasks)} spreadsheets',
            'warnings': errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Error syncing data: {e}")
        return jsonify({'error': 'Failed to sync data'}), 500 