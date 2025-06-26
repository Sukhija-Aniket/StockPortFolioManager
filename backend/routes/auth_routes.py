from flask import Blueprint, redirect, session, request, jsonify
from services.google_service import GoogleService
from services.user_service import UserService
from config import Config
from stock_portfolio_shared.utils.sheet_manager import SheetsManager
from utils.logging_config import setup_logging

logger = setup_logging(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
google_service = GoogleService()
user_service = UserService()
sheets_manager = SheetsManager()

@auth_bp.route('/authorize')
def authorize():
    """Initiate Google OAuth flow"""
    try:
        authorization_url, state = google_service.get_authorization_url(state=None)
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        return jsonify({'error': 'Authorization failed'}), 500

@auth_bp.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback from Google"""
    try:
        # Verify state parameter
        if not session.get('state') == request.args.get('state'):
            return redirect(f"http://{Config.FRONTEND_SERVICE}/")
        
        # Exchange code for token
        credentials = google_service.exchange_code_for_token(request.url)
        
        # Get user profile
        profile = google_service.get_user_profile(credentials)
        
        # Get or create user
        user = user_service.get_or_create_user(profile)
        
        # Store credentials and user info in session
        session['credentials'] = sheets_manager.credentials_to_dict(credentials)
        logger.info("session['credentials']: %s", session['credentials'])
        session['user'] = user_service.create_session_data(user)
        
        return redirect(f"http://{Config.FRONTEND_SERVICE}/")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(f"http://{Config.FRONTEND_SERVICE}/?error=auth_failed")

@auth_bp.route('/user')
def get_user_data():
    """Get current user data"""
    try:
        user = session.get('user')
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        return jsonify(user)
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout')
def logout():
    """Logout user and clear session"""
    try:
        logger.info("=== LOGOUT PROCESS STARTED ===")
        
        # Clear session data
        session.clear()
        
       # Redirect to frontend - this is more reliable for session clearing
        response = jsonify({'message': 'Logged out successfully', 'redirect': True})
        
        # Delete cookie with proper attributes
        response.delete_cookie('session', path='/')
        
        logger.info("Logout completed")
        return response
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/debug-session')
def debug_session():
    """Debug session cookie attributes"""
    
    logger.info("=== SESSION DEBUG ===")
    logger.info("Session data: %s", dict(session))
    logger.info("All cookies: %s", dict(request.cookies))
    
    session_cookie = request.cookies.get('session')
    if session_cookie:
        logger.info("Session cookie full value: %s", session_cookie)
    else:
        logger.info("No session cookie found")
    
    # Check if user is logged in
    user = session.get('user')
    if user:
        logger.info("User is logged in: %s", user)
    else:
        logger.info("No user in session")
    
    return jsonify({
        'session_data': dict(session),
        'cookies': dict(request.cookies),
        'session_cookie_exists': bool(session_cookie),
        'user_logged_in': bool(user),
        'user_data': user
    })