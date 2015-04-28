from os import environ
from . import create_app

if 'DATABASE_URL' not in environ:
  host = environ.get('DB_PORT_5432_TCP_ADDR', '')
  port = environ.get('DB_PORT_5432_TCP_PORT', '')
  db = environ.get('DB_DATABASENAME', '')

  environ['DATABASE_URL'] = "postgresql://postgres@%s/%s" % (host, db)

print environ['DATABASE_URL']

app = create_app(environ)
