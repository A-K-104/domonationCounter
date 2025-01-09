import requests
import time
from datetime import datetime, timezone
import os
from app import create_app
import threading
import webbrowser
from classes.database.db import db
from bs4 import BeautifulSoup


def wait_for_user(message="Press Enter to continue..."):
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        print("\nSimulation interrupted by user")
        os._exit(0)


def start_test_server():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test_key",
            "SESSION_TYPE": "filesystem",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()

    app.run(port=5001)


def extract_session_id(html_content):
    """Extract session ID from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Find the last manage session button which should be for our newly created session
    manage_btns = soup.find_all("button", onclick=lambda x: x and "games-menu?id=" in x)
    if manage_btns:
        onclick = manage_btns[-1]["onclick"]
        # Extract ID from onclick="redirectPage('/games-menu?id=1')"
        session_id = onclick.split("id=")[1].strip("')\">")
        return session_id
    return None


def keep_alive_station(base_url, session_id, station_id, stop_event):
    """Keep a station alive by sending periodic pings."""
    while not stop_event.is_set():
        try:
            requests.get(
                f"{base_url}/live-station?id={session_id}&station-id={station_id}"
            )
            time.sleep(1)  # Send keep-alive every second
        except Exception as e:
            print(f"Error in keep-alive for station {station_id}: {str(e)}")


def simulate_game():
    server_thread = None
    try:
        stop_event = threading.Event()
        keep_alive_threads = []

        # Step 1: Start test server
        print("Step 1: Starting test server...")
        server_thread = threading.Thread(target=start_test_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(2)  # Wait for server to start

        BASE_URL = "http://localhost:5001"

        # Step 2: Create a new session
        print("\nStep 2: Creating new session...")
        session_name = (
            f"Test Session {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        response = requests.post(
            f"{BASE_URL}/home",
            data={"gameSessionName": session_name, "create": "create"},
        )

        # Get the session ID
        response = requests.get(f"{BASE_URL}/home")
        session_id = extract_session_id(response.text)
        if not session_id:
            raise Exception("Failed to get session ID")
        print(f"Session ID: {session_id}")

        # Open session page
        webbrowser.open(f"{BASE_URL}/games-menu?id={session_id}")
        wait_for_user(
            "Session created. Examine the session page and press Enter to add teams..."
        )

        # Add teams
        print("\nAdding teams...")
        teams_data = [
            {"team_name": "Red Team", "team_color": "#ff0000"},
            {"team_name": "Blue Team", "team_color": "#0000ff"},
        ]
        for team in teams_data:
            response = requests.post(f"{BASE_URL}/teams?id={session_id}", data=team)
            print(f"Added team {team['team_name']}")

        webbrowser.open(f"{BASE_URL}/teams?id={session_id}")
        wait_for_user(
            "Teams added. Examine the teams page and press Enter to add stations..."
        )

        # Step 3: Add stations
        print("\nStep 3: Adding stations...")
        stations_data = [
            {
                "stations_name": "Alpha",
                "stations_point": "10",
                "bonus_time_seconds": "30",
            },
            {
                "stations_name": "Beta",
                "stations_point": "15",
                "bonus_time_seconds": "45",
            },
        ]

        for station in stations_data:
            response = requests.post(
                f"{BASE_URL}/stations?id={session_id}", data=station
            )
            if response.status_code == 200:
                print(f"Added station {station['stations_name']}")
            else:
                print(f"Failed to add station {station['stations_name']}")

        webbrowser.open(f"{BASE_URL}/stations?id={session_id}")
        wait_for_user(
            "Stations added. Examine the stations page and press Enter to start the game..."
        )

        # Start keep-alive threads for all stations
        print("\nStarting station keep-alive threads...")
        for i, _ in enumerate(stations_data, 1):
            thread = threading.Thread(
                target=keep_alive_station, args=(BASE_URL, session_id, i, stop_event)
            )
            thread.daemon = True
            thread.start()
            keep_alive_threads.append(thread)
            print(f"Started keep-alive for station {i}")

        # Step 4: Start a new game
        print("\nStep 4: Starting new game...")
        response = requests.get(f"{BASE_URL}/new-game?id={session_id}")
        time.sleep(1)  # Wait for game to be created

        # Get the running game page
        response = requests.get(f"{BASE_URL}/run-game?id={session_id}")
        game_id = session_id  # The game ID is the same as the session ID for takeovers
        print(f"Game ID: {game_id}")

        webbrowser.open(f"{BASE_URL}/run-game?id={session_id}")
        wait_for_user(
            "Game started. Examine the running game page and press Enter to start takeovers..."
        )

        # Step 5: Simulate some takeovers
        print("\nStep 5: Simulating takeovers...")
        takeovers = [
            {
                "station_id": 1,
                "team_id": 1,
                "delay": 0,
                "description": "Red Team takes Alpha",
            },
            {
                "station_id": 2,
                "team_id": 2,
                "delay": 5,
                "description": "Blue Team takes Beta",
            },
            {
                "station_id": 1,
                "team_id": 2,
                "delay": 10,
                "description": "Blue Team takes Alpha",
            },
            {
                "station_id": 2,
                "team_id": 1,
                "delay": 15,
                "description": "Red Team takes Beta",
            },
        ]

        for takeover in takeovers:
            if takeover["delay"] > 0:
                print(f"\nWaiting {takeover['delay']} seconds...")
                time.sleep(takeover["delay"])

            print(f"\nExecuting takeover: {takeover['description']}")
            response = requests.get(
                f"{BASE_URL}/live-station/takeover",
                params={
                    "session-id": session_id,
                    "station-id": takeover["station_id"],
                    "team-id": takeover["team_id"],
                },
            )
            if response.status_code == 200:
                print(f"Takeover successful: {takeover['description']}")
            else:
                print(f"Takeover failed: {response.status_code}")

            # Check station status
            response = requests.get(
                f"{BASE_URL}/live-station",
                params={"session-id": session_id, "station-id": takeover["station_id"]},
            )
            print("Station status checked")

            # Check game score
            response = requests.get(f"{BASE_URL}/run-game/get-score?id={session_id}")
            if response.status_code == 200:
                score_data = response.json()
                print("\nCurrent scores:")
                print(f"Game score: {score_data['gameScore']}")
                print(f"Station score: {score_data['stationScore']}")
                print(f"Team bonus: {score_data['team_bonus']}")

            time.sleep(2)  # Wait a bit to see the changes

        # Stop the game
        response = requests.get(f"{BASE_URL}/run-game/stop", params={"id": session_id})
        if response.status_code == 200:
            print("\nGame stopped successfully")
        else:
            print("\nFailed to stop the game")

        # Display final URLs
        print("\nFinal URLs for monitoring:")
        print(f"- Live Game: {BASE_URL}/run-game?id={session_id}")
        print(f"- Old Games: {BASE_URL}/old-games?id={session_id}")
        print(f"- Teams: {BASE_URL}/teams?id={session_id}")
        print(f"- Stations: {BASE_URL}/stations?id={session_id}")

        # Open final pages
        webbrowser.open(f"{BASE_URL}/old-games?id={session_id}")

        # Keep the main thread running for a while to observe the final state
        print("\nWaiting 30 seconds to observe final state...")
        time.sleep(30)

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
    finally:
        # Clean up threads and server
        print("\nCleaning up...")
        stop_event.set()
        for thread in keep_alive_threads:
            thread.join(timeout=1)
        if server_thread and server_thread.is_alive():
            os._exit(0)  # Force exit to stop Flask server


def main():
    simulate_game()


if __name__ == "__main__":
    main()
