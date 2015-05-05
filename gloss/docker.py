from os import environ
from . import create_app

if 'DATABASE_URL' not in environ:
    host = environ.get('DB_PORT_5432_TCP_ADDR', '')
    port = environ.get('DB_PORT_5432_TCP_PORT', '')
    db = environ.get('DB_DATABASENAME', '')

    pswd = environ.get('DB_PASS', '')
    if pswd != '':
        pswd = ":" + pswd

    environ['DATABASE_URL'] = "postgresql://postgres%s@%s/%s" % (pswd, host, db)

print environ['DATABASE_URL']

app = create_app(environ)
