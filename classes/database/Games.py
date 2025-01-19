"""Games database model."""
from datetime import datetime, timezone
from classes.database.db import db


class Games(db.Model):
    """Games database model."""

    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)
    active = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_ended = db.Column(db.DateTime, nullable=True)

    # Relationships
    stations_take_overs = db.relationship(
        "StationsTakeOvers",
        backref=db.backref("game", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __init__(self, active: bool = True, session: int = None) -> None:
        """Initialize a new game.

        Args:
            active (bool): Whether the game is active
            session (int): ID of the game session this game belongs to
        """
        self.active = active
        self.session = session
        self.start_time = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return string representation of the game."""
        return f"<Game {self.id}>"
