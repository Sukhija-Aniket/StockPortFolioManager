from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.email

class Spreadsheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.String(120), nullable=False)
    spreadsheet_id = db.Column(db.String(200), nullable=False)
    user = db.relationship('User', backref=db.backref('spreadsheets', lazy=True))

    def __repr__(self):
        return '<Spreadsheet %r>' % self.title
    
def configure_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Replace with your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
    db.init_app(app)
    with app.app_context():
        db.create_all()
        
    return db
