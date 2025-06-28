from flask import Blueprint, request, jsonify, session
from stock_portfolio_shared.models.spreadsheet_type import SpreadsheetType
from stock_portfolio_shared.models.spreadsheet_task import SpreadsheetTask
from stock_portfolio_shared.models.depository_participant import DepositoryParticipant
from services.data_service import DataService
from services.spreadsheet_service import SpreadsheetService
from utils.google_api_wrapper import GoogleAuthError
from auth import require_auth
from utils.logging_config import setup_logging
import os
import tempfile

logger = setup_logging(__name__)

data_bp = Blueprint('data', __name__, url_prefix='/data')
data_service = DataService()
spreadsheet_service = SpreadsheetService()


def _get_spreadsheet_id(spreadsheet_url):
    """
    Get spreadsheet ID from URL
    """
    return spreadsheet_url.split('/d/')[1].split('/')[0]

def _spreadsheet_to_task(spreadsheet_data, credentials):
    """
    Convert spreadsheet data to SpreadsheetTask object
    
    Args:
        spreadsheet_data (dict): Spreadsheet data containing url, title, metadata, etc.
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
    
    # Extract metadata from spreadsheet_data (already validated during creation)
    metadata = spreadsheet_data.get('metadata', {})
    
    # Create SpreadsheetTask with metadata
    task = SpreadsheetTask(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_type=SpreadsheetType.SHEETS,
        credentials=credentials,
        title=title,
        metadata=metadata
    )
    
    return task

@data_bp.route('/add', methods=['POST'])
@require_auth
def add_data():
    """Add data to spreadsheet - supports multiple files"""
    try:
        user = session.get('user')
        credentials = session.get('credentials')
        
        # TODO: Improve for not adding already existing data.
        # TODO: Improve for adding data for grow from other brokers.
        # TODO: Taxation Calculation is done not on the final amount but on the amount before brokerage.
        # TODO: Add one more page where I sort by share, and show the taxation data for each sell transaction.
        # TODO: fix the api to fetch current price of the share.
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Get spreadsheet ID from form data
        spreadsheet_url = request.form.get('spreadsheet_url')
        spreadsheet_id = _get_spreadsheet_id(spreadsheet_url)
        if not spreadsheet_id:
            return jsonify({'error': 'Spreadsheet ID is required'}), 400
        
        # Verify spreadsheet ownership
        spreadsheet = spreadsheet_service.get_spreadsheet_by_id(spreadsheet_id, user['id'])
        if not spreadsheet:
            return jsonify({'error': 'Spreadsheet not found or access denied'}), 404
        
        # Create spreadsheet data for task conversion
        spreadsheet_data = {
            'url': spreadsheet_url,
            'title': request.form.get('title') or spreadsheet.title,
            'metadata': spreadsheet.get_metadata()
        }
        
        # Use the utility function to create task
        try:
            spreadsheet_task = _spreadsheet_to_task(spreadsheet_data, credentials)
        except ValueError as e:
            return jsonify({'error': f'Invalid spreadsheet data: {e}'}), 400
        except Exception as e:
            logger.error(f"Error creating spreadsheet task: {e}")
            return jsonify({'error': 'Failed to create task'}), 500
        
        # Process each file
        results = []
        temp_files = []
        
        for i, file in enumerate(files):
            file_result = {
                'filename': file.filename,
                'success': False,
                'message': '',
                'index': i
            }
            
            try:
                # Validate file
                data_service.validate_file_upload(file)
                
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                
                # Process the file
                data_service.process_data_upload(temp_file_path, spreadsheet_task)
                
                file_result['success'] = True
                file_result['message'] = 'File processed successfully'
                results.append(file_result)
                
            except ValueError as e:
                file_result['message'] = f'Validation error: {str(e)}'
                results.append(file_result)
                logger.warning(f"File validation failed for {file.filename}: {e}")
                
            except Exception as e:
                file_result['message'] = f'Processing error: {str(e)}'
                results.append(file_result)
                logger.error(f"Error processing file {file.filename}: {e}")
        
        # Clean up temporary files
        for temp_file_path in temp_files:
            if os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
        
        # Determine overall success
        successful_files = [r for r in results if r['success']]
        failed_files = [r for r in results if not r['success']]
        
        if not successful_files:
            return jsonify({
                'error': 'All files failed to process',
                'details': results
            }), 400
        
        if failed_files:
            # Some files failed
            return jsonify({
                'message': f'Processed {len(successful_files)} out of {len(files)} files successfully',
                'successful': len(successful_files),
                'failed': len(failed_files),
                'details': results
            }), 207  # Multi-Status
        
        # All files succeeded
        return jsonify({
            'message': f'All {len(files)} files processed successfully',
            'successful': len(successful_files),
            'failed': 0,
            'details': results
        })
        
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for add_data: {e}")
        return jsonify({'error': 'Authentication required'}), 401
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
        
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for sync_data: {e}")
        return jsonify({'error': 'Authentication required'}), 401
    except Exception as e:
        logger.error(f"Error syncing data: {e}")
        return jsonify({'error': 'Failed to sync data'}), 500 