from flask import Flask
import os, sys
from flask_cors import CORS

parent_directory = os.path.dirname(os.path.dirname(__file__))
scripts_directory = os.path.join(parent_directory, 'scripts')
sys.path.append(parent_directory)

from dotenv import load_dotenv
env_file = os.path.join(parent_directory, 'secrets', '.env')
load_dotenv(env_file)

from backend.database import db
from backend.routes import initialize_routes

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('APP_SECRET_KEY')
app_port=os.getenv('PORT')

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # allows to use http otherwise https is required
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Replace with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
db.init_app(app)
with app.app_context():
    db.create_all()

initialize_routes(app)
if __name__ == '__main__':
    app.run('localhost', port=int(app_port), debug=True)
