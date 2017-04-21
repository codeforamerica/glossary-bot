from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy

gloss = Blueprint('gloss', __name__)
db = SQLAlchemy()

def create_app(environ):
    app = Flask(__name__)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = environ['DATABASE_URL']
    app.config['DATABASE_URL'] = environ['DATABASE_URL']
    app.config['SLACK_TOKEN'] = environ['SLACK_TOKEN']
    app.config['SLACK_WEBHOOK_URL'] = environ['SLACK_WEBHOOK_URL']

    db.init_app(app)

    app.register_blueprint(gloss)
    return app

from . import views, errors
