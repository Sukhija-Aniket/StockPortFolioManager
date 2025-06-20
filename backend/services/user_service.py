import logging
from extensions import db
from models.user import User
from services.google_service import GoogleService

logger = logging.getLogger(__name__)

class UserService:
    """Service class for handling user-related operations"""
    
    def __init__(self):
        self.google_service = GoogleService()
    
    def get_or_create_user(self, profile):
        """Get existing user or create new one from Google profile"""
        try:
            email = profile['email']
            google_id = profile['id']
            name = profile['name']
            
            user = User.query.filter_by(email=email).first()
            
            if not user:
                user = User(email=email, name=name, google_id=google_id)
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new user: {email}")
            else:
                # Update user information if needed
                if user.name != name or user.google_id != google_id:
                    user.name = name
                    user.google_id = google_id
                    db.session.commit()
                    logger.info(f"Updated user: {email}")
            
            return user
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            db.session.rollback()
            raise
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            return User.query.filter_by(email=email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise
    
    def create_session_data(self, user):
        """Create session data for user"""
        return {
            'name': user.name,
            'email': user.email,
            'google_id': user.google_id,
            'id': user.id
        } 