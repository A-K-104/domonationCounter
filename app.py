import logging
import os
from routes.basicRoutsHandling import basic_routs_handling
from logging import INFO
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_session import Session
from flasgger import Swagger
import constance

from classes.database.db import db
from classes.database.GameSession import GameSession
from classes.database.Games import Games
from classes.database.stations import Stations
from classes.database.stationsTakeOvers import StationsTakeOvers
from classes.database.teams import Teams


def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        # Load the default configuration from constance
        app.config.update(constance.default_config)
        
        # Ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass
    else:
        # Load the test config if passed in
        app.config.update(test_config)
    
    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()
    Session(app)
    Swagger(app, template=constance.swagger_template)
    
    # Register blueprints
    app.register_blueprint(basic_routs_handling)
    
    # Setup logging
    try:
        os.makedirs('logs')
    except OSError:
        pass
        
    file_handler = RotatingFileHandler('logs/errorLog.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    formatter = logging.Formatter("%(asctime)s, level: %(levelname)s:  %(message)s", datefmt='%Y-%m-%d, %H:%M:%S')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(INFO)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
