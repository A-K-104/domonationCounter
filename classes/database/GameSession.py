from datetime import datetime
from flask import session
from classes.database.db import db


class GameSession(db.Model):
    __tablename__ = "game_session"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean(), default=False, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    bonus_minimum_hold = db.Column(db.Integer(), default=20, nullable=False)

    # Define relationships with lazy='dynamic' for better query control
    games = db.relationship(
        "Games", backref=db.backref("session_ref", lazy=True), lazy="dynamic"
    )
    teams = db.relationship(
        "Teams", backref=db.backref("session_ref", lazy=True), lazy="dynamic"
    )
    stations = db.relationship(
        "Stations", backref=db.backref("session_ref", lazy=True), lazy="dynamic"
    )

    def __repr__(self):
        return "<Name %r>" % self.id


def checkIfInSession():
    return session.__contains__("gameSessionName")
