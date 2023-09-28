# init.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
from flask_bootstrap import Bootstrap5
from config import Config
from flask_migrate import Migrate

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    bootstrap = Bootstrap5(app)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate = Migrate(app, db)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from app.auth import bp as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.register import bp as register_blueprint
    app.register_blueprint(register_blueprint)
    
    return app
