"""Basic route handling for the application."""
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect
from flasgger import swag_from

from classes.database.models import (
    GameSession,
    Games,
    Stations,
    Teams,
    StationsTakeOvers,
)
from classes.database.db import db

basic_routs_handling = Blueprint("basic_routs_handling", __name__)


@basic_routs_handling.route("/", methods=["GET", "POST"])
@swag_from("../swagger_docs/base_get.yml", methods=["GET"])
def baseRoute():
    """Base route that redirects to home."""
    return redirect("/home")


@basic_routs_handling.route("/home", methods=["GET", "POST"])
@swag_from("../swagger_docs/home_get.yml", methods=["GET"])
@swag_from("../swagger_docs/home_post.yml", methods=["POST"])
def home():
    """Home page route."""
    if request.method == "POST":
        if request.form.get("gameSessionName"):
            if request.form.get("create"):
                if (
                    db.session.query(GameSession)
                    .filter_by(name=request.form["gameSessionName"])
                    .first()
                    is None
                ):
                    new_game = GameSession(name=request.form["gameSessionName"])
                    db.session.add(new_game)
                    db.session.commit()
            elif request.form.get("edit"):
                game_session = GameSession.query.get(request.form["edit"])
                if game_session:
                    game_session.name = request.form["gameSessionName"]
                    db.session.commit()

        elif request.form.get("removeGameId"):
            game = GameSession.query.get(request.form["removeGameId"])
            if game:
                db.session.delete(game)
                db.session.commit()
        elif request.form.get("disableEnableGame"):
            game = GameSession.query.get(request.form["disableEnableGame"])
            if game:
                game.active = not game.active
                db.session.commit()

    games_sessions = GameSession.query.all()
    return render_template("home.html", gamesSessions=games_sessions)


@basic_routs_handling.route("/enterPage", methods=["GET", "POST"])
@swag_from("../swagger_docs/enter_page_get.yml", methods=["GET"])
def game_pome_page():
    if request.args.__contains__("messages"):
        return render_template("enterPage.html", messages=request.args.get("messages"))
    return render_template("enterPage.html")


@basic_routs_handling.route("/games-menu", methods=["GET", "POST"])
@swag_from("../swagger_docs/games_menu_get.yml", methods=["GET"])
def games_menu():
    if (
        not request.args.__contains__("id")
        or db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
        is None
    ):
        return redirect("/")

    return render_template("gameHomePage.html", id=request.args.get("id"))


@basic_routs_handling.route("/update-session-bonus/<sessionId>", methods=["POST"])
@swag_from("../swagger_docs/update_session_bonus_post.yml", methods=["POST"])
def update_session_bonus(sessionId):
    game_session = db.session.query(GameSession).filter_by(id=sessionId).first()
    game_session.bonus_minimum_hold = request.json["bonus_minimum_hold"]
    db.session.commit()

    return "updated successfully"


@basic_routs_handling.route("/teams", methods=["GET", "POST"])
@swag_from("../swagger_docs/teams_get.yml", methods=["GET"])
@swag_from("../swagger_docs/teams_post.yml", methods=["POST"])
def teams_handler():
    """Handle team management."""
    session_id = request.args.get("id") or request.form.get("session_id")
    if not session_id:
        return redirect("/")

    game_session = GameSession.query.filter_by(id=session_id).first()
    if game_session is None:
        return redirect("/")

    message = ""
    if request.method == "POST":
        if request.form.get("team_name") and request.form.get("team_color"):
            # Check if team name exists
            existing_team = Teams.query.filter_by(
                name=request.form["team_name"], session=game_session.id
            ).first()

            if existing_team:
                message = "name already exist"
            else:
                # Check if color exists
                existing_color = Teams.query.filter_by(
                    color=request.form["team_color"], session=game_session.id
                ).first()

                if existing_color:
                    message = "color already exist"
                else:
                    # Create new team
                    new_team = Teams(
                        name=request.form["team_name"],
                        color=request.form["team_color"],
                        session=game_session.id,
                    )
                    db.session.add(new_team)
                    db.session.commit()

        elif request.form.get("removeTeamId"):
            team = Teams.query.get(request.form["removeTeamId"])
            if (
                team and team.session == game_session.id
            ):  # Verify team belongs to session
                db.session.delete(team)
                db.session.commit()
        else:
            message = "Missing required fields"

    return render_template(
        "teams.html",
        teams=list(game_session.teams),
        message=message,
        id=game_session.id,
    )


@basic_routs_handling.route("/log_to_game", methods=["GET", "POST"])
@swag_from("../swagger_docs/log_to_game_get.yml", methods=["GET"])
@swag_from("../swagger_docs/log_to_game_post.yml", methods=["POST"])
def log_to_game():
    if request.method == "POST":
        game = GameSession.query.get(request.form["game_id"])
        if game is None:
            return redirect("/home?messages=wrong_error_code")
        if game.active:
            return redirect(f"/live-game?game-id={game.id}")
        else:
            return redirect(f"/home?messages=game_{game.id}_is_not_active")
    return redirect("/home?messages=wrong_method")


@basic_routs_handling.route("/old-games", methods=["GET", "POST"])
@swag_from("../swagger_docs/old_games_get.yml", methods=["GET"])
def old_games():
    """Old games page route."""
    session_id = request.args.get("id")
    if not session_id:
        game_sessions = GameSession.query.all()
        return render_template("old_games.html", game_sessions=game_sessions)

    game_session = GameSession.query.filter_by(id=session_id).first()
    if not game_session:
        return redirect("/old-games")

    games = Games.query.filter_by(active=False, session=session_id).all()
    games_score = []

    for game in games:
        score, last_teams, team_bonus = calc_game(game_session, game)
        score_dict = {}
        for team in game_session.teams:
            team_score = score.get(team.id, 0)
            score_dict[team.name] = {"score": team_score, "color": team.color}

        last_teams_dict = {}
        for station_id, station_data in last_teams.items():
            team = next(
                (t for t in game_session.teams if t.id == station_data.get("team")),
                None,
            )
            last_teams_dict[station_id] = {
                "name": station_data.get("name"),
                "teamName": team.name if team else "N/A",
                "color": team.color if team else "#000000",
            }

        games_score.append(
            {
                "score": score_dict,
                "lastTeams": last_teams_dict,
                "id": game.id,
                "team_bonus": team_bonus,
            }
        )

    return render_template(
        "old_games.html",
        game_sessions=GameSession.query.all(),
        gamesScore=games_score,
        id=session_id,
        sessionId=session_id,
    )


@basic_routs_handling.route("/old-games/re-calc", methods=["GET", "POST"])
@swag_from("../swagger_docs/old_games_recalc_get.yml", methods=["GET"])
def re_calc_game():
    """Recalculate game scores."""
    if not request.args.__contains__("game-id") or not request.args.__contains__("id"):
        return redirect("/")

    game = Games.query.get(request.args["game-id"])
    game_session = GameSession.query.filter_by(id=request.args["id"]).first()

    if game is None or game_session is None:
        return redirect("/")

    score, last_teams, team_bonus = calc_game(game_session, game)

    # Convert score to use team names instead of IDs
    score_dict = {}
    for team in game_session.teams:
        team_score = score.get(team.id, 0)
        score_dict[team.name] = {"score": team_score, "color": team.color}

    # Convert last teams to use team names
    last_teams_dict = {}
    for station_id, station_data in last_teams.items():
        team = next(
            (t for t in game_session.teams if t.id == station_data.get("team")), None
        )
        last_teams_dict[station_id] = {
            "name": station_data.get("name"),
            "teamName": team.name if team else "N/A",
            "color": team.color if team else "#000000",
        }

    game.game_score = {
        "score": score_dict,
        "lastTeams": last_teams_dict,
        "team_bonus": team_bonus,
        "id": game.id,
    }

    db.session.commit()
    return redirect(f"/old-games?id={game_session.id}")


@basic_routs_handling.route("/stations", methods=["GET", "POST"])
@swag_from("../swagger_docs/stations_get.yml", methods=["GET"])
@swag_from("../swagger_docs/stations_post.yml", methods=["POST"])
def stations():
    if (
        not request.args.__contains__("id")
        or db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
        is None
    ):
        return redirect("/")

    game_session = (
        db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    )
    message = ""
    if request.method == "POST":
        if request.form.__contains__("stations_name") and request.form.__contains__(
            "stations_point"
        ):
            if (
                db.session.query(Stations)
                .filter_by(
                    name=request.form["stations_name"], session=request.args.get("id")
                )
                .first()
                is None
            ):
                new_stations = Stations(
                    name=request.form["stations_name"],
                    point=request.form["stations_point"],
                    bonus_time_seconds=request.form["bonus_time_seconds"],
                )
                game_session.stations.append(new_stations)
                db.session.commit()
            else:
                message = "name already exist"
        else:
            message = "failed to get par"
    session_stations = (
        db.session.query(Stations).filter_by(session=request.args.get("id")).all()
    )
    return render_template(
        "stations.html",
        stations=list(session_stations),
        message=message,
        id=request.args.get("id"),
    )


@basic_routs_handling.route("/stations/remove", methods=["POST", "GET"])
@swag_from("../swagger_docs/stations_remove_get.yml", methods=["GET"])
def remove_station():
    if (
        not request.args.__contains__("id")
        or db.session.query(GameSession).filter_by(id=request.args["id"]).first()
        is None
    ):
        return redirect("/")

    if request.args.__contains__("removeStationId"):
        station = GameSession.query.get(request.args["removeStationId"])
        if station is not None:
            db.session.delete(station)
            db.session.commit()

    return redirect(f"/stations?id={request.args['id']}")


@basic_routs_handling.route("/stations/edit", methods=["POST"])
@swag_from("../swagger_docs/stations_edit_post.yml", methods=["POST"])
def edit_station():
    if (
        not request.args.__contains__("id")
        or not request.args.__contains__("stationId")
        or not request.form.__contains__("stations_point")
    ):
        return redirect("/stations")

    game_session: GameSession = (
        db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    )
    station: GameSession = (
        db.session.query(GameSession)
        .filter_by(id=request.args.get("stationId"))
        .first()
    )

    if game_session is None or station is None:
        return redirect("/stations")
    station.point = request.form["stations_point"]
    station.bonus_time_seconds = request.form["bonus_time_seconds"]
    db.session.commit()

    return redirect(f"/stations?id={request.args['id']}")


@basic_routs_handling.route("/live-game", methods=["GET", "POST"])
@swag_from("../swagger_docs/live_game_get.yml", methods=["GET"])
@swag_from("../swagger_docs/live_game_post.yml", methods=["POST"])
def live_game():
    if (
        not request.args.__contains__("session-id")
        or db.session.query(GameSession)
        .filter_by(id=request.args["session-id"])
        .first()
        is None
    ):
        return redirect("/")

    game_session = (
        db.session.query(GameSession).filter_by(id=request.args["session-id"]).first()
    )
    return render_template(
        "live_game.html",
        stations=list(game_session.stations),
        gameId=request.args["session-id"],
    )


@basic_routs_handling.route("/live-station", methods=["GET"])
@swag_from("../swagger_docs/live_station_get.yml", methods=["GET"])
def live_station():
    game_id, game_session = get_game_id_from_re(request)
    station: Stations = (
        db.session.query(Stations).filter_by(id=request.args["station-id"]).first()
    )
    if station is None or game_session is None:
        return redirect("/")

    connected = True
    # Ensure last_ping is timezone-aware
    last_ping = (
        station.last_ping
        if station.last_ping.tzinfo
        else station.last_ping.replace(tzinfo=timezone.utc)
    )
    if not (
        station.connected
        and (datetime.now(timezone.utc) - last_ping).total_seconds() / 60 < 2
    ) or request.args.__contains__("alerted"):
        station.connected = True
        station.last_ping = datetime.now(timezone.utc)
        db.session.commit()
        connected = False

    team_in_con_id = -1
    if game_id is not None:
        team_in_con_id = int(team_in_control(game_id, int(request.args["station-id"])))
    team_in_con = (
        db.session.query(Teams)
        .filter_by(id=team_in_con_id, session=game_session.id)
        .first()
    )

    return render_template(
        "live_station.html",
        teams=list(game_session.teams),
        sessionId=request.args["session-id"],
        stationName=station.name,
        stationId=station.id,
        teamInControl=team_in_con,
        connected=connected,
    )


@basic_routs_handling.route("/live-station/takeover", methods=["GET"])
@swag_from("../swagger_docs/live_station_takeover_get.yml", methods=["GET"])
def live_station1():
    game_id, game_session = get_game_id_from_re(request)

    if game_id is None or game_session is None:
        return redirect("/games-menu?id=" + request.args.get("session-id", ""))

    if not request.args.__contains__("team-id") or not request.args.__contains__(
        "station-id"
    ):
        return redirect("/games-menu?id=" + request.args.get("session-id", ""))

    game = Games.query.get(game_id.id)
    if game:
        # Create takeover with current UTC time
        take_over = StationsTakeOvers(
            station_id=request.args["station-id"],
            team_id=request.args["team-id"],
            game_id=game.id,
            date_created=datetime.now(timezone.utc),
        )
        db.session.add(take_over)
        db.session.commit()

    return redirect(
        f'/live-station?session-id={game_session.id}'
        f'&station-id={request.args["station-id"]}&alerted=true'
    )


@basic_routs_handling.route("/new-game", methods=["GET", "POST"])
@swag_from("../swagger_docs/new_game_get.yml", methods=["GET"])
@swag_from("../swagger_docs/new_game_post.yml", methods=["POST"])
def new_game():
    if not request.args.__contains__("id"):
        return redirect("/")

    game_session = GameSession.query.filter_by(id=request.args.get("id")).first()
    if game_session is None:
        return redirect("/")

    for game in game_session.games:
        if game.active:
            stop_running_game(game, game_session)

    new_game = Games(active=True, session=game_session.id)
    game_session.games.append(new_game)
    db.session.commit()
    return redirect(f"/run-game?id={game_session.id}")


@basic_routs_handling.route("/run-game", methods=["GET", "POST"])
@swag_from("../swagger_docs/run_game_get.yml", methods=["GET"])
def running_game_manage():
    if not request.args.__contains__("id"):
        return redirect("/")

    game_session = GameSession.query.filter_by(id=request.args.get("id")).first()
    if game_session is None:
        return redirect("/")

    running_game = multi_games_running(game_session.games)
    if running_game is None:
        return redirect(f"/games-menu?id={game_session.id}")

    if request.method == "POST":
        stop_running_game(running_game, game_session)

    return render_template(
        "manageRunningGame.html",
        teams=game_session.teams,
        id=request.args.get("id"),
        stations=game_session.stations,
    )


@basic_routs_handling.route("/run-game/stop", methods=["GET", "POST"])
@swag_from("../swagger_docs/run_game_stop_get.yml", methods=["GET"])
def running_game_stop():
    if (
        not request.args.__contains__("id")
        or db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
        is None
    ):
        return redirect("/")

    game_session = (
        db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    )
    running_game: GameSession = multi_games_running(game_session.games)
    if running_game is None:
        return "error multiply games are running or none"
    stop_running_game(running_game, game_session)
    return redirect(f"/games-menu?id={game_session.id}")


@basic_routs_handling.route("/run-game/get-score", methods=["GET", "POST"])
@swag_from("../swagger_docs/run_game_get_score_get.yml", methods=["GET"])
def running_game_get_live():
    if (
        not request.args.__contains__("id")
        or db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
        is None
    ):
        return {"status": 400, "error": "failed to find session"}, 400
    game_session = (
        db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    )

    calc_station_status(game_session)

    # Check if there are any games in the session
    games = list(game_session.games)
    if not games:
        return {"status": 400, "error": "no games found in session"}, 400

    game_score, station_score, team_bonus = calc_game(game_session, games[-1], True)
    return {
        "gameScore": game_score,
        "stationScore": station_score,
        "team_bonus": team_bonus,
    }


@basic_routs_handling.route("/enter-to-session", methods=["GET", "POST"])
@swag_from("../swagger_docs/enter_to_session_get.yml", methods=["GET"])
def enter_to_session():
    if (
        not request.form.__contains__("gameSessionId")
        or db.session.query(GameSession)
        .filter_by(id=request.form["gameSessionId"])
        .first()
        is None
    ):
        return redirect("/")

    game_session = (
        db.session.query(GameSession)
        .filter_by(id=request.form["gameSessionId"])
        .first()
    )
    return redirect(f"/live-game?session-id={game_session.id}")


@basic_routs_handling.route("/game-is-alive", methods=["GET"])
@swag_from("../swagger_docs/game_is_alive_get.yml", methods=["GET"])
def game_is_alive() -> (str, int):
    if not request.args.__contains__("session-id") or not request.args.__contains__(
        "station-id"
    ):
        return "false", 400

    game_session: GameSession = (
        db.session.query(GameSession).filter_by(id=request.args["session-id"]).first()
    )
    station: GameSession = (
        db.session.query(GameSession)
        .filter_by(id=request.args["station-id"], session=request.args["session-id"])
        .first()
    )

    if station is None or game_session is None:
        return "false", 400

    station.last_ping = datetime.now(timezone.utc)
    if not station.connected:
        station.connected = True
    db.session.commit()

    if len(game_session.games) > 0 and game_session.games[-1].date_ended is None:
        team = team_in_control(game_session.games[-1], int(request.args["station-id"]))
        found_team: GameSession = (
            db.session.query(GameSession)
            .filter_by(id=team, session=request.args["session-id"])
            .first()
        )

        if found_team is not None:
            team_color: str = found_team.color
        else:
            team_color = "#FFFFFF"

        return {"color": team_color, "teamId": team}, 200
    return "false", 202


@basic_routs_handling.route("/game_home_page", methods=["GET"])
@swag_from("../swagger_docs/game_home_page_get.yml", methods=["GET"])
def game_home_page():
    """Render the game home page."""
    game_sessions = GameSession.query.all()
    return render_template("gameHomePage.html", game_sessions=game_sessions)


def multi_games_running(games: list) -> None or GameSession:
    running_game: GameSession or None = None
    for game in games:
        if game.active:
            if running_game is not None:
                return None
            running_game = game
    return running_game


def team_in_control(game: GameSession, station_id: int):
    team_in = (
        db.session.query(StationsTakeOvers)
        .filter_by(game_id=game.id, station_id=station_id)
        .order_by(StationsTakeOvers.date_created.desc())
        .first()
    )

    if team_in is not None:
        return team_in.team_id
    return -1


def calc_game(game_session: GameSession, game: GameSession, for_running_game=False) -> (
    None,
    None,
) or (dict, dict):
    result: dict = {}
    team_bonus: dict = {}
    last_team_dict: dict = {}
    for team in game_session.teams:
        result[team.id] = 0

    game_ended = game.date_ended
    if game_ended is None:
        game_ended = datetime.now(timezone.utc)
    if for_running_game:
        for station in game_session.stations:
            last_team_dict[station.id] = {
                "name": station.name,
                "team": "N/A",
                "color": "#000000",
                "teamName": "N/A",
                "connected": station.connected,
                "lastPing": station.last_ping,
            }
    for station in game_session.stations:
        sub_result, last_team = station_calc(
            game_session.teams,
            station,
            game.stations_take_overs,
            game_ended,
            game_session,
            team_bonus,
        )
        team: Teams = db.session.query(Teams).filter_by(id=last_team).first()
        if team is not None:
            if for_running_game:
                last_team_dict[station.id] = {
                    "name": station.name,
                    "team": last_team,
                    "color": team.color,
                    "teamName": team.name,
                    "connected": station.connected,
                    "lastPing": station.last_ping,
                }
            else:
                last_team_dict[station.id] = {
                    "name": station.name,
                    "team": last_team,
                    "color": team.color,
                    "teamName": team.name,
                }
        for team in game_session.teams:
            result[team.id] += sub_result[team.id]
    return result, last_team_dict, team_bonus


def get_list_of_take_overs_per_station(station: GameSession, take_overs: list) -> list:
    new_take_over: list = []
    for take_over in take_overs:
        if take_over.station_id == station.id:
            new_take_over.append(take_over)
    return new_take_over


def station_calc(
    teams: list,
    station: GameSession,
    take_overs: list,
    game_ended: datetime,
    game_session: GameSession,
    team_bonus: dict,
) -> (None, None) or (dict, int):
    result: dict = {}
    last_take_over: datetime or None = None
    pre_team: int or None = None
    bonus_enabled: bool = False

    # Ensure game_ended is timezone-aware
    if not game_ended.tzinfo:
        game_ended = game_ended.replace(tzinfo=timezone.utc)

    for team in teams:
        result[team.id] = 0

    take_overs = get_list_of_take_overs_per_station(station, take_overs)
    if len(take_overs) > 0:
        for take_over in take_overs:
            # Ensure take_over date is timezone-aware
            if not take_over.date_created.tzinfo:
                take_over.date_created = take_over.date_created.replace(
                    tzinfo=timezone.utc
                )

            if result.__contains__(take_over.team_id):
                if last_take_over is not None and pre_team is not None:
                    # Calculate points for previous team's control duration
                    duration_minutes = (
                        take_over.date_created - last_take_over
                    ).total_seconds() / 60
                    points = duration_minutes * station.point
                    result[pre_team] += points

                    # Calculate bonus if applicable
                    result[pre_team] += station_bonus_calc(
                        bonus_enabled,
                        int((take_over.date_created - last_take_over).total_seconds()),
                        pre_team,
                        station,
                        game_session,
                        team_bonus,
                        teams,
                    )

                # Check if bonus should be enabled
                if (
                    not bonus_enabled
                    and pre_team is not None
                    and (take_over.date_created - last_take_over).total_seconds()
                    >= game_session.bonus_minimum_hold
                ):
                    bonus_enabled = True

                last_take_over = take_over.date_created
            pre_team = take_over.team_id

        # Calculate points for the last team's control duration
        if last_take_over is not None:
            duration_minutes = (game_ended - last_take_over).total_seconds() / 60
            points = duration_minutes * station.point
            result[take_overs[-1].team_id] += points

            # Calculate final bonus if applicable
            result[take_overs[-1].team_id] += station_bonus_calc(
                bonus_enabled,
                int((game_ended - last_take_over).total_seconds()),
                take_overs[-1].team_id,
                station,
                game_session,
                team_bonus,
                teams,
            )

    return result, pre_team


def get_team_by_id(session_teams: list, team_id) -> GameSession or None:
    for team in session_teams:
        if team.id == team_id:
            return team
    return None


def get_game_id_from_re(game_request):
    """Get game ID from request."""
    if not game_request.args.__contains__("session-id"):
        return None, None

    game_session = GameSession.query.filter_by(
        id=game_request.args["session-id"]
    ).first()
    if game_session is None:
        return None, None

    running_game = multi_games_running(game_session.games)
    return running_game, game_session


def stop_running_game(running_game: GameSession, game_session: GameSession) -> None:
    running_game.date_ended = datetime.now(timezone.utc)
    game_res, last_teams, team_bonus = calc_game(game_session, running_game)
    game_res = convert_team_id_to_team_name_dict(game_res, game_session.teams)

    running_game.game_score = {
        "score": game_res,
        "lastTeams": last_teams,
        "team_bonus": team_bonus,
        "id": running_game.id,
    }

    running_game.active = False
    db.session.commit()


def convert_team_id_to_team_name_dict(game_score: dict, teams: list) -> dict:
    new_dict: dict = {}
    for score in game_score:
        for team in teams:
            if team.id == score:
                new_dict[team.name] = {
                    "score": round(game_score[score], 2),
                    "color": team.color,
                }
    return new_dict


def calc_station_status(game_session: GameSession):
    game_stations: list = game_session.stations
    for station in game_stations:
        # Ensure last_ping is timezone-aware
        last_ping = (
            station.last_ping
            if station.last_ping.tzinfo
            else station.last_ping.replace(tzinfo=timezone.utc)
        )
        if (datetime.now(timezone.utc) - last_ping).seconds / 60 > 2:
            station.connected = False
        else:
            station.connected = True
    db.session.commit()


def station_bonus_calc(
    bonus_enabled: bool,
    holding_time: int,
    team_id,
    station: GameSession,
    game_session: GameSession,
    team_bonus: dict,
    session_teams: list,
) -> int:
    team_name = get_team_by_id(session_teams, team_id).name
    if bonus_enabled and (holding_time >= game_session.bonus_minimum_hold):
        if not team_bonus.get(team_name) or not team_bonus[team_name].__contains__(
            station.name
        ):
            team_bonus[team_name] = (team_bonus.get(team_name) or []) + [station.name]
            return station.bonus_time_seconds * station.point / 60
    return 0
