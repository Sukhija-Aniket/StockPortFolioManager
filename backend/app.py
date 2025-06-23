import os
from flask import Flask, jsonify
from sqlalchemy import text
from config import config
from extensions import db, cors
from routes.auth_routes import auth_bp
from routes.spreadsheet_routes import spreadsheet_bp
from routes.data_routes import data_bp
from utils.logging_config import setup_logging

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set OAuth transport setting
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = app.config.get('OAUTHLIB_INSECURE_TRANSPORT', '0')
    
    # Initialize extensions
    db.init_app(app)
    cors.init_app(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
    
    # Setup logging
    setup_logging(__name__)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(spreadsheet_bp)
    app.register_blueprint(data_bp)
    
    # Health check endpoint for Docker
    @app.route('/health')
    def health_check():
        """Health check endpoint for Docker health checks"""
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))
            return jsonify({
                'status': 'healthy',
                'service': 'backend',
                'database': 'connected'
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'backend',
                'error': str(e)
            }), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run('0.0.0.0', port=port, debug=True)
