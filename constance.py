from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LJADLKCDDFD425344dfhW'
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gameData.db'
app.config['SQLALCHEMY_BINDS'] = {'stations': 'sqlite:///gameData.db', 'games': 'sqlite:///gameData.db'}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Swagger configuration
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Domination Counter API",
        "description": "API documentation for the Domination Counter game management system",
        "version": "1.0",
        "contact": {
            "name": "Domination Counter Support",
        }
    },
    "tags": [
        {
            "name": "Game Sessions",
            "description": "Game session management operations"
        },
        {
            "name": "Game Management",
            "description": "Operations for managing active games"
        },
        {
            "name": "Station Management",
            "description": "Operations for managing game stations"
        },
        {
            "name": "Team Management",
            "description": "Operations for managing teams"
        },
        {
            "name": "Game History",
            "description": "Operations for viewing and managing past games"
        },
        {
            "name": "Navigation",
            "description": "Basic navigation endpoints"
        }
    ],
    "schemes": ["http", "https"]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "title": "Domination Counter API Documentation"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)
sess = Session(app)
db = SQLAlchemy(app)
#  sudo gunicorn3 -w 4 --reload -b localhost:5000 denominationCounter:app