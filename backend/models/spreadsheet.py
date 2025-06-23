from extensions import db
from datetime import datetime, timezone

class Spreadsheet(db.Model):
    """Spreadsheet model for storing spreadsheet information"""
    __tablename__ = 'spreadsheets'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_created = db.Column(db.String(120), nullable=False)
    spreadsheet_id = db.Column(db.String(200), nullable=False, unique=True)
    data_hash = db.Column(db.String(200), nullable=True) # hash of the data in the spreadsheet
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationship
    user = db.relationship('User', backref=db.backref('spreadsheets', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Spreadsheet {self.title}>'
    
    def to_dict(self):
        """Convert spreadsheet to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'spreadsheet_id': self.spreadsheet_id,
            'url': f'https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}',
            'date_created': self.date_created,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 