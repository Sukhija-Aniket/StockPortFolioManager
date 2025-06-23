from flask import Blueprint, request, jsonify, session
from services.spreadsheet_service import SpreadsheetService
from services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

spreadsheet_bp = Blueprint('spreadsheet', __name__, url_prefix='/spreadsheets')
spreadsheet_service = SpreadsheetService()
user_service = UserService()

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@spreadsheet_bp.route('/', methods=['GET'])
@require_auth
def get_spreadsheets():
    """Get all spreadsheets for current user"""
    try:
        user = session.get('user')
        spreadsheets = spreadsheet_service.get_user_spreadsheets(user['email'])
        
        if spreadsheets is None:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(spreadsheets)
        
    except Exception as e:
        logger.error(f"Error getting spreadsheets: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@spreadsheet_bp.route('/', methods=['POST'])
@require_auth
def create_spreadsheet():
    """Create a new spreadsheet"""
    try:
        user = session.get('user')
        credentials = session.get('credentials')
        
        if not credentials:
            return jsonify({'error': 'No credentials found'}), 401
        
        data = request.get_json()
        title = data.get('title')
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        spreadsheet = spreadsheet_service.create_spreadsheet(
            user['id'], 
            title, 
            credentials
        )
        
        return jsonify(spreadsheet), 201
        
    except Exception as e:
        logger.error(f"Error creating spreadsheet: {e}")
        return jsonify({'error': 'Failed to create spreadsheet'}), 500

@spreadsheet_bp.route('/<spreadsheet_id>', methods=['DELETE'])
@require_auth
def delete_spreadsheet(spreadsheet_id):
    """Delete a spreadsheet"""
    try:
        user = session.get('user')
        credentials = session.get('credentials')
        
        if not credentials:
            return jsonify({'error': 'No credentials found'}), 401
        
        spreadsheet_service.delete_spreadsheet(
            user['id'], 
            spreadsheet_id, 
            credentials
        )
        
        return jsonify({'message': 'Spreadsheet deleted successfully'})
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting spreadsheet: {e}")
        return jsonify({'error': 'Failed to delete spreadsheet'}), 500 