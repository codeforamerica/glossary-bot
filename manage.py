from os import environ, path
from gloss import create_app, db
from gloss.models import Definition, Interaction
from flask.ext.script import Manager, Shell

# grab environment variables from the .env file if it exists
if path.exists('.env'):
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            environ[var[0]] = var[1]

app = create_app(environ)
manager = Manager(app)

def make_shell_context():
    return dict(app=app, db=db, Definition=Definition, Interaction=Interaction)
manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
