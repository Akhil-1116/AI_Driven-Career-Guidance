from flask import Flask
from flask_pymongo import PyMongo
import os

mongo = PyMongo()  # Create mongo outside so we can init it later

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config["MONGO_URI"] = "mongodb://localhost:27017/career_db"

    # Initialize MongoDB with app
    mongo.init_app(app)

    # Register Blueprints
    from app.routes import auth  # Make sure your blueprint is in routes.py
    app.register_blueprint(auth)

    return app
