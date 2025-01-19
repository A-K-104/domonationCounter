"""Test fixtures."""
import pytest
from app import create_app
from classes.database.db import db
from classes.database.game_session import GameSession
from classes.database.games import Games
from classes.database.stations import Stations
from classes.database.teams import Teams


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create the app with test config
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test_key",
            "SESSION_TYPE": "filesystem",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Create the database and load test data
    with app.app_context():
        db.create_all()

        # Create test game session
        test_session = GameSession(name="Test Session", active=True)
        db.session.add(test_session)
        db.session.commit()

        # Create test teams
        team1 = Teams(name="Team 1", color="red", session=test_session.id)
        team2 = Teams(name="Team 2", color="blue", session=test_session.id)
        db.session.add_all([team1, team2])
        db.session.commit()

        # Create test stations
        station1 = Stations(
            name="Station 1", point=10, bonus_time_seconds=30, session=test_session.id
        )
        station2 = Stations(
            name="Station 2", point=20, bonus_time_seconds=60, session=test_session.id
        )
        db.session.add_all([station1, station2])
        db.session.commit()

        # Create test game
        test_game = Games(session=test_session.id, active=True)
        db.session.add(test_game)
        db.session.commit()

    yield app

    # Clean up database
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def session(app):
    """Create a database session."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        session = db.session

        yield session

        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def game_session(session):
    """Create a test game session."""
    session = GameSession(name="Test Session")
    db.session.add(session)
    db.session.commit()
    return session


@pytest.fixture
def team(session, game_session):
    """Create a test team."""
    team = Teams(name="Red Team", color="#ff0000", session=game_session.id)
    db.session.add(team)
    db.session.commit()
    return team


@pytest.fixture
def station(session, game_session):
    """Create a test station."""
    station = Stations(
        name="Alpha", point=10, bonus_time_seconds=30, session=game_session.id
    )
    db.session.add(station)
    db.session.commit()
    return station
