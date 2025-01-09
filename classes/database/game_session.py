"""Game session database model."""
from datetime import datetime, timezone
from flask import session
from classes.database.db import db


class GameSession(db.Model):
    """Game session model for managing game sessions."""

    __tablename__ = "game_session"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean(), default=False, nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    bonus_minimum_hold = db.Column(db.Integer(), default=20, nullable=False)

    # Define relationships with lazy='dynamic' for better query control
    games = db.relationship(
        "Games",
        backref=db.backref("game_session", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    teams = db.relationship(
        "Teams",
        backref=db.backref("game_session", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    stations = db.relationship(
        "Stations",
        backref=db.backref("game_session", lazy=True),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return string representation of the game session."""
        return f"<GameSession {self.name}>"


def check_if_in_session() -> bool:
    """Check if a game session exists in the current session."""
    return "gameSessionName" in session
