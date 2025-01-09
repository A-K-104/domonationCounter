"""Stations database model."""
from datetime import datetime, timezone
from classes.database.db import db


class Stations(db.Model):
    """Stations database model."""

    __tablename__ = "stations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    point = db.Column(db.Integer, nullable=False)
    bonus_time_seconds = db.Column(db.Integer, nullable=False)
    connected = db.Column(db.Boolean(), default=False, nullable=False)
    last_ping = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    session = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)

    # Relationships
    take_overs = db.relationship(
        "StationsTakeOvers",
        backref=db.backref("station", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __init__(
        self, name: str, point: int, bonus_time_seconds: int, session: int
    ) -> None:
        """Initialize a new station."""
        self.name = name
        self.point = point
        self.bonus_time_seconds = bonus_time_seconds
        self.session = session

    def __repr__(self) -> str:
        """Return string representation of the station."""
        return f"<Station {self.name}>"
