from . import gloss as app
from . import db
from flask import abort, current_app, request

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    return 'you are authorized!', 200
