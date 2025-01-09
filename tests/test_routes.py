import pytest


def test_base_redirect(client):
    """Test that the base route redirects to home."""
    response = client.get("/")
    assert response.status_code == 302
    assert b"/home" in response.data


def test_home_page(client):
    """Test that the home page loads correctly."""
    response = client.get("/home")
    assert response.status_code == 200


def test_game_home_page(client):
    """Test that the game home page loads correctly."""
    response = client.get("/game_home_page")
    assert response.status_code == 200


def test_old_games(client):
    """Test that the old games page loads correctly."""
    response = client.get("/old-games")
    assert response.status_code == 200


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
