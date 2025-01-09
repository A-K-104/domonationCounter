"""Test database models."""
from datetime import datetime, timezone
from classes.database.models import (
    GameSession,
    Games,
    Stations,
    Teams,
    StationsTakeOvers,
)
from classes.database.db import db


def test_game_session_model(app):
    """Test GameSession model."""
    with app.app_context():
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        assert session.id is not None
        assert session.name == "Test Session"
        assert session.active is True
        assert session.bonus_minimum_hold == 20  # Default value is 20
        assert session.date_created is not None


def test_games_model(app):
    """Test Games model."""
    with app.app_context():
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        game = Games(session=session.id, active=True)
        db.session.add(game)
        db.session.commit()

        assert game.id is not None
        assert game.session == session.id
        assert game.active is True
        assert game.date_ended is None


def test_teams_model(app):
    """Test Teams model."""
    with app.app_context():
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        team = Teams(name="Red Team", color="#ff0000", session=session.id)
        db.session.add(team)
        db.session.commit()

        assert team.id is not None
        assert team.name == "Red Team"
        assert team.color == "#ff0000"
        assert team.session == session.id


def test_stations_model(app):
    """Test Stations model."""
    with app.app_context():
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        station = Stations(
            name="Alpha", point=10, bonus_time_seconds=30, session=session.id
        )
        db.session.add(station)
        db.session.commit()

        assert station.id is not None
        assert station.name == "Alpha"
        assert station.point == 10
        assert station.bonus_time_seconds == 30
        assert station.session == session.id
        assert station.connected is False
        assert isinstance(station.last_ping, datetime)


def test_stations_take_overs_model(app):
    """Test StationsTakeOvers model."""
    with app.app_context():
        # Create required related objects
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        team = Teams(name="Red Team", color="#ff0000", session=session.id)
        station = Stations(
            name="Alpha", point=10, bonus_time_seconds=30, session=session.id
        )
        game = Games(session=session.id, active=True)
        db.session.add_all([team, station, game])
        db.session.commit()

        # Create takeover
        takeover = StationsTakeOvers(
            team_id=team.id, station_id=station.id, game_id=game.id
        )
        db.session.add(takeover)
        db.session.commit()

        assert takeover.id is not None
        assert takeover.team_id == team.id
        assert takeover.station_id == station.id
        assert takeover.game_id == game.id
        assert isinstance(takeover.date_created, datetime)


def test_cascade_delete_game_session(app):
    """Test cascade delete of game session."""
    with app.app_context():
        # Create game session
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        # Create related objects
        team = Teams(name="Red Team", color="#ff0000", session=session.id)
        station = Stations(
            name="Alpha", point=10, bonus_time_seconds=30, session=session.id
        )
        game = Games(session=session.id, active=True)
        db.session.add_all([team, station, game])
        db.session.commit()

        # Delete game session
        db.session.delete(session)
        db.session.commit()

        # Verify cascade deletion
        assert Teams.query.filter_by(session=session.id).first() is None
        assert Stations.query.filter_by(session=session.id).first() is None
        assert Games.query.filter_by(session=session.id).first() is None


def test_station_connection_status(app):
    """Test station connection status."""
    with app.app_context():
        session = GameSession(name="Test Session", active=True)
        db.session.add(session)
        db.session.commit()

        station = Stations(
            name="Alpha", point=10, bonus_time_seconds=30, session=session.id
        )
        db.session.add(station)
        db.session.commit()

        # Test default values
        assert station.connected is False
        assert isinstance(station.last_ping, datetime)

        # Test updating connection status
        station.connected = True
        station.last_ping = datetime.now(timezone.utc)
        db.session.commit()

        assert station.connected is True
        assert isinstance(station.last_ping, datetime)
