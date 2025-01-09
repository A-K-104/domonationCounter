"""Games database model."""
from datetime import datetime

from classes.database.db import db


class Games(db.Model):
    """Games database model."""

    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)
    active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, session: int, active: bool = True) -> None:
        """Initialize a new game."""
        self.session = session
        self.active = active
        self.start_time = datetime.now()

    def __repr__(self) -> str:
        """Return string representation of the game."""
        return f"<Game {self.id}>"
