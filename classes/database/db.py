from flask_sqlalchemy import SQLAlchemy
from flask import current_app

# Create the SQLAlchemy instance
db = SQLAlchemy()

def get_db():
    """Get the database instance."""
    return db
