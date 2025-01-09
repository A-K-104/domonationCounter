from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy instance
db = SQLAlchemy()


def get_db():
    """Get the database instance."""
    return db
