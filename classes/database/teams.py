from datetime import datetime
from classes.database.db import db


class Teams(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    session = db.Column(db.Integer, db.ForeignKey("game_session.id"), nullable=False)

    take_overs = db.relationship("StationsTakeOvers", backref="team", lazy=True)

    def __repr__(self):
        return "<Name %r>" % self.id
