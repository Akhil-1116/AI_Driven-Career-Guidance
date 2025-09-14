from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env file

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # Correct usage of environment variable
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
    
    mongo.init_app(app)
    
    from app.routes import auth
    app.register_blueprint(auth)

    return app
