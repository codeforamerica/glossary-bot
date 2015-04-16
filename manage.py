from os import environ, path
from gloss import create_app, db
from gloss.models import Definition, Interaction
from flask.ext.script import Manager, prompt_bool
from flask.ext.migrate import Migrate, MigrateCommand

# grab environment variables from the .env file if it exists
if path.exists('.env'):
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            environ[var[0]] = var[1]

app = create_app(environ)
manager = Manager(app)

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.shell
def make_shell_context():
    return dict(app=app, db=db, Definition=Definition, Interaction=Interaction)

@manager.command
def runtests():
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=1).run(tests)

@manager.command
def dropdb():
    if prompt_bool("Are you sure you want to lose all your data?"):
        db.drop_all()

@manager.command
def createdb():
    db.create_all()

if __name__ == '__main__':
    manager.run()
