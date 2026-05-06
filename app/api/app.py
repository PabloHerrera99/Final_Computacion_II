import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask
from app.api.config import Config
from app.api.database import init_database
from app.api.routes.auth import auth_bp
from app.api.routes.matches import matches_bp
from app.api.routes.stats import stats_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(auth_bp)
    app.register_blueprint(matches_bp)
    app.register_blueprint(stats_bp)
    return app

if __name__ == '__main__':
    init_database()
    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)