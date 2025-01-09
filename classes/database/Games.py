from datetime import datetime
from classes.database.db import db
import constance
from classes.database.GameSession import GameSession

class Games(db.Model):
    __tablename__ = 'games'

    # to init db in terminal type: python ->from app import db->db.create_all()-> exit(). and you are set!
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_ended = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean(), default=False, nullable=False)
    game_score = db.Column(db.JSON, default={})
    session = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)

    stations_take_overs = db.relationship('StationsTakeOvers', backref='game', lazy=True)

    def __repr__(self):
        return '<Name %r>' % self.id


def checkIfInSession():
    if not ('email' in session):
        return False
    return True
