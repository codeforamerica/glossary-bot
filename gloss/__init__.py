from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy
import re

gloss = Blueprint('gloss', __name__)
db = SQLAlchemy()

def create_app(environ):
    app = Flask(__name__)

    # SQLAlchemy no longer recognizes postgres:// URLs as "postgresql"
    # https://github.com/sqlalchemy/sqlalchemy/issues/6083
    uri = environ["DATABASE_URL"]
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['DATABASE_URL'] = uri
    app.config['SLACK_TOKEN'] = environ['SLACK_TOKEN']
    app.config['SLACK_WEBHOOK_URL'] = environ['SLACK_WEBHOOK_URL']

    db.init_app(app)

    app.register_blueprint(gloss)
    return app

from . import views, errors
