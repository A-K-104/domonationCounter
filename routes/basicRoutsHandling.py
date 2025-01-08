import constance
from datetime import datetime
from flask import Blueprint, render_template, request
from werkzeug.utils import redirect
from flasgger import swag_from

from classes.database.GameSession import GameSession
from classes.database.Games import Games
from classes.database.stations import Stations
from classes.database.stationsTakeOvers import StationsTakeOvers
from classes.database.teams import Teams

basic_routs_handling = Blueprint('basic_routs_handling', __name__)
app = constance.app
db = constance.db


@basic_routs_handling.route('/', methods=['GET', 'POST'])
@swag_from('../swagger_docs/base_get.yml', methods=['GET'])
def baseRoute():
    return redirect("/home")


@basic_routs_handling.route('/home', methods=['GET', 'POST'])
@swag_from('../swagger_docs/home_get.yml', methods=['GET'])
@swag_from('../swagger_docs/home_post.yml', methods=['POST'])
def home():
    game_session_name = None
    method = 'create'
    if request.method == "POST":
        if request.form.__contains__("gameSessionName"):
            if request.form.__contains__('create'):
                if db.session.query(GameSession).filter_by(name=request.form["gameSessionName"]).first() is None:
                    new_game = GameSession(name=request.form["gameSessionName"])
                    db.session.add(new_game)
            elif request.form.__contains__('edit'):
                if db.session.query(GameSession).filter_by(name=request.form["gameSessionName"]).first() is None:
                    game_session_name = GameSession.query.get(request.form["edit"])
                    game_session_name.name = request.form["gameSessionName"]

        elif request.form.__contains__("removeGameId"):
            game = GameSession.query.get(request.form["removeGameId"])
            db.session.delete(game)
        elif request.form.__contains__("disableEnableGame"):
            game = GameSession.query.get(request.form["disableEnableGame"])
            game.active = not game.active
        elif request.form.__contains__("manageGame"):
            game_session_name = GameSession.query.get(request.form["manageGame"])
            method = 'edit'
        db.session.commit()

    games_sessions = GameSession.query.all()
    return render_template("home.html", gamesSessions=games_sessions, method=method, gameSessionName=game_session_name)


@basic_routs_handling.route('/enterPage', methods=['GET', 'POST'])
@swag_from('../swagger_docs/enter_page_get.yml', methods=['GET'])
def game_pome_page():
    if request.args.__contains__("messages"):
        return render_template("enterPage.html", messages=request.args.get("messages"))
    return render_template("enterPage.html")


@basic_routs_handling.route('/games-menu', methods=['GET', 'POST'])
@swag_from('../swagger_docs/games_menu_get.yml', methods=['GET'])
def games_menu():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")

    return render_template("gameHomePage.html", id=request.args.get("id"))


@basic_routs_handling.route('/update-session-bonus/<sessionId>', methods=['POST'])
@swag_from('../swagger_docs/update_session_bonus_post.yml', methods=['POST'])
def update_session_bonus(sessionId):
    game_session = db.session.query(GameSession).filter_by(id=sessionId).first()
    game_session.bonus_minimum_hold = request.json['bonus_minimum_hold']
    db.session.commit()

    return "updated successfully"


@basic_routs_handling.route('/teams', methods=['GET', 'POST'])
@swag_from('../swagger_docs/teams_get.yml', methods=['GET'])
@swag_from('../swagger_docs/teams_post.yml', methods=['POST'])
def teams_handler():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    message = ""
    if request.method == "POST":
        if request.form.__contains__('team_name') and request.form.__contains__('team_color'):
            if db.session.query(Teams). \
                    filter_by(name=request.form['team_name'], session=request.args.get("id")).first() is None:
                if db.session.query(Teams). \
                        filter_by(color=request.form['team_color'], session=request.args.get("id")).first() is None:
                    new_teams = Teams(name=request.form['team_name'], color=request.form['team_color'])
                    game_session.teams.append(new_teams)
                    db.session.commit()
                else:
                    message = "color already exist"
            else:
                message = "name already exist"
        elif request.form.__contains__('removeTeamId'):
            team = Teams.query.get(request.form['removeTeamId'])
            if team is not None:
                db.session.delete(team)
                db.session.commit()
        else:
            message = "failed to get par"
    session_teams = db.session.query(Teams).filter_by(session=request.args.get("id")).all()
    return render_template("teams.html", teams=list(session_teams), message=message, id=request.args.get("id"))


@basic_routs_handling.route('/log_to_game', methods=['GET', 'POST'])
@swag_from('../swagger_docs/log_to_game_get.yml', methods=['GET'])
@swag_from('../swagger_docs/log_to_game_post.yml', methods=['POST'])
def log_to_game():
    if request.method == "POST":
        game = Games.query.get(request.form["game_id"])
        if game is None:
            return redirect(f"/home?messages=wrong_error_code")
        if game.active:
            return redirect(f"/live-game?game-id={game.id}")
        else:
            return redirect(f"/home?messages=game_{game.id}_is_not_active")
    return redirect(f"/home?messages=wrong_method")


@basic_routs_handling.route('/old-games', methods=['GET', 'POST'])
@swag_from('../swagger_docs/old_games_get.yml', methods=['GET'])
def old_games():
    if not request.args.__contains__('id'):
        return redirect("/")
    game_session: GameSession = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()

    if game_session is None:
        return redirect("/")

    games_score: list = []
    game: Games
    for game in game_session.games:
        if not game.active:
            if game.game_score == {}:
                return redirect(f"/old-games/re-calc?game-id={game.id}&id={game_session.id}")
            game.game_score['score'] = dict(sorted(game.game_score['score'].items(), key=lambda item: item[1]['score'], reverse=True))
            games_score.append(game.game_score)

    return render_template("old_games.html", gamesScore=games_score,
                           sessionId=game_session.id, id=request.args.get("id"))


@basic_routs_handling.route('/old-games/re-calc', methods=['GET', 'POST'])
@swag_from('../swagger_docs/old_games_recalc_get.yml', methods=['GET'])
def re_calc_game():
    if not request.args.__contains__('game-id') or not request.args.__contains__('id'):
        return redirect("/")
    game: Games = db.session.query(Games).filter_by(id=request.args["game-id"]).first()
    game_session: GameSession = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    if game is None or game_session is None:
        return redirect("/")
    game_res, last_teams, team_bonus = calc_game(game_session, game)
    game_res = convert_team_id_to_team_name_dict(game_res, game_session.teams)
    game.game_score = {"score": game_res, "lastTeams": last_teams, "team_bonus": team_bonus, "id": game.id}

    db.session.commit()
    return redirect(f"/old-games?id={game_session.id}")


@basic_routs_handling.route('/stations', methods=['GET', 'POST'])
@swag_from('../swagger_docs/stations_get.yml', methods=['GET'])
@swag_from('../swagger_docs/stations_post.yml', methods=['POST'])
def stations():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    message = ""
    if request.method == "POST":
        if request.form.__contains__('stations_name') and request.form.__contains__('stations_point'):
            if db.session.query(Stations).filter_by(name=request.form['stations_name'],
                                                    session=request.args.get("id")).first() is None:
                new_stations = Stations(name=request.form['stations_name'], point=request.form['stations_point'],
                                        bonus_time_seconds=request.form['bonus_time_seconds'])
                game_session.stations.append(new_stations)
                db.session.commit()
            else:
                message = "name already exist"
        else:
            message = "failed to get par"
    session_station = db.session.query(Stations).filter_by(session=request.args.get("id")).all()
    return render_template("stations.html", stations=list(session_station), message=message, id=request.args.get("id"))


@basic_routs_handling.route('/stations/remove', methods=['POST', 'GET'])
@swag_from('../swagger_docs/stations_remove_get.yml', methods=['GET'])
def remove_station():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args["id"]).first() is None:
        return redirect("/")

    if request.args.__contains__('removeStationId'):
        station = Stations.query.get(request.args['removeStationId'])
        if station is not None:
            db.session.delete(station)
            db.session.commit()

    return redirect(f"/stations?id={request.args['id']}")


@basic_routs_handling.route('/stations/edit', methods=['POST'])
@swag_from('../swagger_docs/stations_edit_post.yml', methods=['POST'])
def edit_station():
    if not request.args.__contains__('id') or \
            not request.args.__contains__('stationId') or \
            not request.form.__contains__('stations_point'):
        return redirect("/stations")

    game_session: GameSession = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    station: Stations = db.session.query(Stations).filter_by(id=request.args.get("stationId")).first()

    if game_session is None or station is None:
        return redirect("/stations")
    station.point = request.form['stations_point']
    station.bonus_time_seconds = request.form['bonus_time_seconds']
    db.session.commit()

    return redirect(f"/stations?id={request.args['id']}")


@basic_routs_handling.route('/live-game', methods=['GET', 'POST'])
@swag_from('../swagger_docs/live_game_get.yml', methods=['GET'])
@swag_from('../swagger_docs/live_game_post.yml', methods=['POST'])
def live_game():
    message = ""
    if not request.args.__contains__("session-id") or \
            db.session.query(GameSession).filter_by(id=request.args["session-id"]).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args["session-id"]).first()
    return render_template("live_game.html", stations=list(game_session.stations), message=message,
                           gameId=request.args['session-id'])


@basic_routs_handling.route('/live-station', methods=['GET'])
@swag_from('../swagger_docs/live_station_get.yml', methods=['GET'])
def live_station():
    game_id, game_session = get_game_id_from_re(request)
    station: Stations = db.session.query(Stations).filter_by(id=request.args["station-id"]).first()
    if station is None or game_session is None:
        return redirect("/")
    connected = True
    if not (station.connected and (datetime.utcnow() - station.last_ping).seconds / 60 < 2) \
            or request.args.__contains__("alerted"):
        station.connected = True
        station.last_ping = datetime.utcnow()
        db.session.commit()
        connected = False

    team_in_con_id = -1
    if game_id is not None:
        team_in_con_id = int(team_in_control(game_id, int(request.args['station-id'])))
    team_in_con = db.session.query(Teams).filter_by(id=team_in_con_id, session=game_session.id).first()

    return render_template("live_station.html", teams=list(game_session.teams),
                           sessionId=request.args['session-id'],
                           stationName=station.name, stationId=station.id,
                           teamInControl=team_in_con, connected=connected)


@basic_routs_handling.route('/live-station/takeover', methods=['GET'])
@swag_from('../swagger_docs/live_station_takeover_get.yml', methods=['GET'])
def live_station1():
    game_id, game_session = get_game_id_from_re(request)

    if game_id is not None:
        if not request.args.__contains__("team-id"):
            return redirect('/')
        game = db.session.query(Games).filter_by(id=game_id.id).first()
        game.stationsTakeOvers.append(
            StationsTakeOvers(stationId=request.args['station-id'], teamId=request.args["team-id"]))
        db.session.commit()
    return redirect(f'/live-station?session-id={game_session.id}'
                    f'&station-id={request.args["station-id"]}&alerted=true')


@basic_routs_handling.route('/new-game', methods=['GET', 'POST'])
@swag_from('../swagger_docs/new_game_get.yml', methods=['GET'])
@swag_from('../swagger_docs/new_game_post.yml', methods=['POST'])
def new_game():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    for game in game_session.games:
        if game.active:
            stop_running_game(game, game_session)
    game_session.games.append(Games(active=True))
    db.session.commit()
    return redirect(f"/run-game?id={game_session.id}")


@basic_routs_handling.route('/run-game', methods=['GET', 'POST'])
@swag_from('../swagger_docs/run_game_get.yml', methods=['GET'])
def running_game_manage():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    running_game = multi_games_running(game_session.games)
    if running_game is None:
        return "error multiply games are running or none"
    if request.method == "POST":
        stop_running_game(running_game, game_session)
    return render_template("manageRunningGame.html", teams=game_session.teams, id=request.args.get("id"),
                           stations=game_session.stations)


@basic_routs_handling.route('/run-game/stop', methods=['GET', 'POST'])
@swag_from('../swagger_docs/run_game_stop_get.yml', methods=['GET'])
def running_game_stop():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()
    running_game: Games = multi_games_running(game_session.games)
    if running_game is None:
        return "error multiply games are running or none"
    stop_running_game(running_game, game_session)
    return redirect(f"/games-menu?id={game_session.id}")


@basic_routs_handling.route('/run-game/get-score', methods=['GET', 'POST'])
@swag_from('../swagger_docs/run_game_get_score_get.yml', methods=['GET'])
def running_game_get_live():
    if not request.args.__contains__('id') or \
            db.session.query(GameSession).filter_by(id=request.args.get("id")).first() is None:
        return {"status": 400, "error": "failed to find session"}, 400
    game_session = db.session.query(GameSession).filter_by(id=request.args.get("id")).first()

    calc_station_status(game_session)
    game_score, station_score, team_bonus = calc_game(game_session, game_session.games[-1], True)
    return {"gameScore": game_score, "stationScore": station_score, "team_bonus": team_bonus}


@basic_routs_handling.route('/enter-to-session', methods=['GET', 'POST'])
@swag_from('../swagger_docs/enter_to_session_get.yml', methods=['GET'])
def enter_to_session():
    if not request.form.__contains__('gameSessionId') or \
            db.session.query(GameSession).filter_by(id=request.form["gameSessionId"]).first() is None:
        return redirect("/")
    game_session = db.session.query(GameSession).filter_by(id=request.form["gameSessionId"]).first()
    return redirect(f"/live-game?session-id={game_session.id}")


@basic_routs_handling.route('/game-is-alive', methods=['GET'])
@swag_from('../swagger_docs/game_is_alive_get.yml', methods=['GET'])
def game_is_alive() -> (str, int):
    if not request.args.__contains__("session-id") or not request.args.__contains__("station-id"):
        return "false", 400

    game_session: GameSession = db.session.query(GameSession).filter_by(id=request.args["session-id"]).first()
    station: Stations = db.session.query(Stations).filter_by(id=request.args["station-id"],
                                                             session=request.args["session-id"]).first()

    if station is None or game_session is None:
        return "false", 400

    station.last_ping = datetime.utcnow()
    if not station.connected:
        station.connected = True
    db.session.commit()

    if len(game_session.games) > 0 and game_session.games[-1].date_ended is None:

        team = team_in_control(game_session.games[-1], int(request.args["station-id"]))
        found_team: Teams = db.session.query(Teams).filter_by(id=team, session=request.args["session-id"]).first()

        if found_team is not None:
            team_color: str = found_team.color
        else:
            team_color = "#FFFFFF"

        return {"color": team_color, "teamId": team}, 200
    return "false", 202


def multi_games_running(games: list) -> None or Games:
    running_game: Games or None = None
    for game in games:
        if game.active:
            if running_game is not None:
                return None
            running_game = game
    return running_game


def team_in_control(game: Games, station_id: int):
    team_in = db.session.query(StationsTakeOvers).filter_by(game=game.id, stationId=station_id) \
        .order_by(StationsTakeOvers.date_created.desc()).first()

    if team_in is not None:
        return team_in.teamId
    return -1


def calc_game(game_session: GameSession, game: Games, for_running_game=False) -> (None, None) or (dict, dict):
    if not game_session.games.__contains__(game):
        return None, None
    result: dict = {}
    team_bonus: dict = {}
    last_team_dict: dict = {}
    for team in game_session.teams:
        result[team.id] = 0

    game_ended = game.date_ended
    if game_ended is None:
        game_ended = datetime.utcnow()
    if for_running_game:
        for station in game_session.stations:
            last_team_dict[station.id] = {"name": station.name, "team": "N/A", "color": "#000000",
                                          "teamName": "N/A", "connected": station.connected,
                                          "lastPing": station.last_ping}
    for station in game_session.stations:

        sub_result, last_team = station_calc(game_session.teams, station,
                                             game.stationsTakeOvers, game_ended,
                                             game_session, team_bonus)
        team: Teams = db.session.query(Teams).filter_by(id=last_team).first()
        if team is not None:
            if for_running_game:
                last_team_dict[station.id] = {"name": station.name, "team": last_team, "color": team.color,
                                              "teamName": team.name, "connected": station.connected,
                                              "lastPing": station.last_ping}
            else:
                last_team_dict[station.id] = {"name": station.name, "team": last_team, "color": team.color,
                                              "teamName": team.name}
        for team in game_session.teams:
            result[team.id] += sub_result[team.id]
    return result, last_team_dict, team_bonus


def get_list_of_take_overs_per_station(station: Stations, take_overs: list) -> list:
    new_take_over: list = []
    for take_over in take_overs:
        if take_over.stationId == station.id:
            new_take_over.append(take_over)
    return new_take_over


def station_calc(teams: list, station: Stations, take_overs: list,
                 game_ended: datetime, game_session: GameSession,
                 team_bonus: dict) -> (None, None) or (dict, int):
    result: dict = {}
    last_take_over: datetime or None = None
    pre_team: int or None = None
    bonus_enabled: bool = False
    for team in teams:
        result[team.id] = 0
    take_overs = get_list_of_take_overs_per_station(station, take_overs)
    if len(take_overs) > 0:
        for take_over in take_overs:
            if result.__contains__(take_over.teamId):
                if last_take_over is not None and pre_team is not None:
                    result[pre_team] += (take_over.date_created - last_take_over).seconds / 60 * station.point
                    result[pre_team] += station_bonus_calc(bonus_enabled,
                                                           (take_over.date_created - last_take_over).seconds,
                                                           pre_team, station, game_session, team_bonus, teams)

                if not bonus_enabled and pre_team is not None and \
                        (take_over.date_created - last_take_over).seconds >= game_session.bonus_minimum_hold:
                    bonus_enabled = True
                last_take_over = take_over.date_created

            pre_team = take_over.teamId
        if last_take_over is not None:
            result[take_overs[-1].teamId] += (game_ended - last_take_over).seconds / 60 * station.point + \
                                             station_bonus_calc(bonus_enabled,
                                                                (game_ended - last_take_over).seconds,
                                                                take_overs[-1].teamId, station, game_session, team_bonus, teams)
    return result, pre_team


def station_bonus_calc(bonus_enabled: bool, holding_time: int, team_id,
                       station: Stations, game_session: GameSession, team_bonus: dict, session_teams: list) -> int:
    team_name = get_team_by_id(session_teams, team_id).name
    if bonus_enabled and (holding_time >= game_session.bonus_minimum_hold):
        if not team_bonus.get(team_name) or not team_bonus[team_name].__contains__(station.name):
            team_bonus[team_name] = (team_bonus.get(team_name) or []) + [station.name]
            return station.bonus_time_seconds * station.point / 60
    return 0


def get_team_by_id(session_teams: list, team_id) -> Teams or None:
    for team in session_teams:
        if team.id == team_id:
            return team
    return None


def get_game_id_from_re(game_request) -> (Games, Stations) or (None, None):
    if not game_request.args.__contains__("session-id") or \
            db.session.query(GameSession).filter_by(id=game_request.args["session-id"]).first() is None:
        return None, None

    if not game_request.args.__contains__("station-id") or \
            db.session.query(Stations).filter_by(id=game_request.args["station-id"],
                                                 session=game_request.args["session-id"]).first() is None:
        return None, None

    game_session = db.session.query(GameSession).filter_by(id=game_request.args["session-id"]).first()
    game_id = multi_games_running(game_session.games)
    return game_id, game_session


def stop_running_game(running_game: Games, game_session: GameSession) -> None:
    running_game.date_ended = datetime.utcnow()
    game_res, last_teams, team_bonus = calc_game(game_session, running_game)
    game_res = convert_team_id_to_team_name_dict(game_res, game_session.teams)

    running_game.game_score = {"score": game_res, "lastTeams": last_teams, "team_bonus": team_bonus, "id": running_game.id}

    running_game.active = False
    db.session.commit()


def convert_team_id_to_team_name_dict(game_score: dict, teams: list) -> dict:
    new_dict: dict = {}
    for score in game_score:
        for team in teams:
            if team.id == score:
                new_dict[team.name] = {"score": round(game_score[score], 2),
                                       "color": team.color}
    return new_dict


def calc_station_status(game_session: GameSession):
    game_stations: list = game_session.stations
    for station in game_stations:
        if (datetime.utcnow() - station.last_ping).seconds / 60 > 2:
            station.connected = False
        else:
            station.connected = True
    db.session.commit()
