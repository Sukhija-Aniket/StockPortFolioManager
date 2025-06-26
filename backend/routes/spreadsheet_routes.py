from flask import Blueprint, request, jsonify, session
from services.spreadsheet_service import SpreadsheetService
from stock_portfolio_shared.models.depository_participant import DepositoryParticipant
from utils.google_api_wrapper import GoogleAuthError
from auth import require_auth
from utils.logging_config import setup_logging

logger = setup_logging(__name__)

spreadsheet_bp = Blueprint('spreadsheet', __name__, url_prefix='/spreadsheets')
spreadsheet_service = SpreadsheetService()

@spreadsheet_bp.route('/', methods=['GET'])
@require_auth
def get_spreadsheets():
    """Get all spreadsheets for user"""
    try:
        user = session.get('user')
        spreadsheets = spreadsheet_service.get_spreadsheets(user['id'])
        
        if spreadsheets is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(spreadsheets)
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for get_spreadsheets: {e}")
        return jsonify({'error': 'Authentication required - please sign in again'}), 401
    except Exception as e:
        logger.error(f"Error getting spreadsheets: {e}")
        return jsonify({'error': 'Failed to get spreadsheets'}), 500

@spreadsheet_bp.route('/<spreadsheet_id>', methods=['GET'])
@require_auth
def get_spreadsheet(spreadsheet_id):
    """Get specific spreadsheet"""
    try:
        user = session.get('user')
        spreadsheet = spreadsheet_service.get_spreadsheet_by_id(spreadsheet_id, user['id'])
        if not spreadsheet:
            return jsonify({'error': 'Spreadsheet not found'}), 404
        return jsonify(spreadsheet.to_dict())
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for get_spreadsheet: {e}")
        return jsonify({'error': 'Authentication required - please sign in again'}), 401
    except Exception as e:
        logger.error(f"Error getting spreadsheet: {e}")
        return jsonify({'error': 'Failed to get spreadsheet'}), 500

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
        metadata = data.get('metadata', {})
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        # Validate participant_name if present in metadata
        if metadata and 'participant_name' in metadata:
            participant_name = metadata['participant_name']
            try:
                # Validate participant name against enum
                validated_participant = DepositoryParticipant.from_string(participant_name)
                # Update metadata with validated participant name
                metadata['participant_name'] = validated_participant.value
                logger.info(f"Validated participant name: {validated_participant.value}")
            except Exception as e:
                logger.warning(f"Invalid participant_name '{participant_name}': {e}")
                return jsonify({'error': f'Invalid participant name: {participant_name}'}), 400
        
        spreadsheet = spreadsheet_service.create_spreadsheet(
            user['id'], 
            title, 
            credentials,
            metadata
        )
        
        return jsonify(spreadsheet), 201
        
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for create_spreadsheet: {e}")
        return jsonify({'error': 'Authentication required - please sign in again'}), 401
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
        
        spreadsheet_service.delete_spreadsheet(user['id'], spreadsheet_id, credentials)
        return jsonify({'message': 'Spreadsheet deleted successfully'}), 200
        
    except GoogleAuthError as e:
        logger.warning(f"Authentication required for delete_spreadsheet: {e}")
        return jsonify({'error': 'Authentication required - please sign in again'}), 401
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting spreadsheet: {e}")
        return jsonify({'error': 'Failed to delete spreadsheet'}), 500 