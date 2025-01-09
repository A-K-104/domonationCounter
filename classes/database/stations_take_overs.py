"""StationsTakeOvers database model."""
from datetime import datetime, timezone
from classes.database.db import db


class StationsTakeOvers(db.Model):
    """StationsTakeOvers database model."""

    __tablename__ = "stations_take_overs"

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)

    def __init__(
        self, station_id: int, team_id: int, game_id: int, date_created: datetime = None
    ) -> None:
        """Initialize a new station takeover."""
        self.station_id = station_id
        self.team_id = team_id
        self.game_id = game_id
        if date_created:
            self.date_created = date_created

    def __repr__(self) -> str:
        """Return string representation of the station takeover."""
        return f"<StationTakeOver {self.id}>"
