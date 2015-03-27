from os import environ
from . import create_app

app = create_app(environ)
