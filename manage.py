from os import environ
from gloss import create_app, db
from gloss.models import Definition
from flask.ext.script import Manager, Shell

app = create_app(environ)
manager = Manager(app)

def make_shell_context():
    return dict(app=app, db=db, Definition=Definition)
manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
