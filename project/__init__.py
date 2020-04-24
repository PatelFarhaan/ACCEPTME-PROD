from flask import Flask
from acceptme import Bot
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import create_database, database_exists


bot = Bot
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://farhaan:testpassword@localhost/instamax'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    create_database(app.config['SQLALCHEMY_DATABASE_URI'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.blueprint_login_views = {
    'core': 'core.login',
    'admin': 'admin.login'
}

from project.core.views import core_blueprint
from project.users.views import users_blueprint
from project.admin.views import admins_blueprint
from project.error_pages.handler import error_pages


app.register_blueprint(error_pages)
app.register_blueprint(core_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(admins_blueprint)