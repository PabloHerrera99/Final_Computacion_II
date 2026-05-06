from flask import Flask
from app.api.config import Config
from app.api.database import init_database

from app.api.routes.auth import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_database()
        
    app.register_blueprint(auth_bp)
    
    return app

if __name__ == '__main__':
      app = create_app()
      app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)