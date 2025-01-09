from datetime import datetime
from classes.database.db import db


class Stations(db.Model):
    __tablename__ = 'stations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    point = db.Column(db.Integer, nullable=False)
    bonus_time_seconds = db.Column(db.Integer, nullable=False)
    connected = db.Column(db.Boolean(), default=False, nullable=False)
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)
    session = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)

    take_overs = db.relationship('StationsTakeOvers', backref='station', lazy=True)

    def __repr__(self):
        return '<Name %r>' % self.id


def checkIfInSession():
    if not ('email' in session):
        return False
    return True
