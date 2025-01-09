"""Teams database model."""
from datetime import datetime, timezone
from classes.database.db import db


class Teams(db.Model):
    """Teams database model."""

    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    session = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)

    # Relationships
    take_overs = db.relationship(
        "StationsTakeOvers",
        backref=db.backref("team", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __init__(self, name: str, color: str, session: int) -> None:
        """Initialize a new team."""
        self.name = name
        self.color = color
        self.session = session

    def __repr__(self) -> str:
        """Return string representation of the team."""
        return f"<Team {self.name}>"
