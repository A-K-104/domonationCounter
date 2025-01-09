from datetime import datetime
from classes.database.db import db


class StationsTakeOvers(db.Model):
    __tablename__ = 'stations_take_overs'
    # to init db in terminal type: python ->from app import db->db.create_all()-> exit(). and you are set!
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)

    def __repr__(self):
        return '<Name %r>' % self.id
