from os import environ
from . import create_app

if 'DATABASE_URL' not in environ:
    host = environ.get('DB_PORT_5432_TCP_ADDR', '')
    port = environ.get('DB_PORT_5432_TCP_PORT', '')
    name = environ.get('DB_DATABASENAME', '')
    pswd = environ.get('DB_PASS', '')
    pswd = ":{}".format(pswd) if pswd else ''

    environ['DATABASE_URL'] = "postgresql://postgres{pswd}@{host}/{name}".format(pswd=pswd, host=host, name=name)

print environ['DATABASE_URL']

app = create_app(environ)
