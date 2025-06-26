from functools import wraps
from flask import session, jsonify

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        credentials = session.get('credentials')
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        if not credentials:
            return jsonify({'error': 'No credentials found'}), 401
        return f(*args, **kwargs)
    return decorated_function 