import constance
import logging
from routes.basicRoutsHandling import basic_routs_handling
from logging import INFO
from logging.handlers import RotatingFileHandler


def create():
    db = constance.db
    app = constance.app
    app.register_blueprint(basic_routs_handling)

    file_handler = RotatingFileHandler('logs/errorLog.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    formatter = logging.Formatter("%(asctime)s, level: %(levelname)s:  %(message)s", datefmt='%Y-%m-%d, %H:%M:%S')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(INFO)
    
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create()
    app.run(host='0.0.0.0', port=5000, debug=True)
