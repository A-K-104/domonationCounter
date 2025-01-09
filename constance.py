"""
Global constants and configurations for the Domination Counter application.
"""
import os

# Get the absolute path to the instance folder
INSTANCE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))

# In Docker, the database file should be in the instance folder which is mounted as a volume
DB_PATH = os.path.join(INSTANCE_PATH, "gameData.db")
DB_URI = f'sqlite:///{DB_PATH}'

# Default configuration
default_config = {
    'SECRET_KEY': 'LJADLKCDDFD425344dfhW',
    'SESSION_PERMANENT': False,
    'SESSION_TYPE': 'filesystem',
    'SQLALCHEMY_DATABASE_URI': DB_URI,
    'SQLALCHEMY_BINDS': {
        'stations': DB_URI,
        'games': DB_URI
    },
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}

# Swagger configuration template
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Domonation Counter API",
        "description": "API for managing game sessions and scoring",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ]
}