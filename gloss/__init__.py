from flask import Blueprint, Flask
from flask.ext.sqlalchemy import SQLAlchemy

gloss = Blueprint('gloss', __name__)
db = SQLAlchemy()

def create_app(environ):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = environ['DATABASE_URL']
    app.config['DATABASE_URL'] = environ['DATABASE_URL']
    app.config['SLACK_TOKEN'] = environ['SLACK_TOKEN']

    db.init_app(app)

    app.register_blueprint(gloss)
    return app

from . import views
