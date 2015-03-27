from . import gloss as app
from . import db
from flask import abort, current_app, request

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    params = {'team_id': request.form['team_id'], 'team_domain': request.form['team_domain'], 'channel_id': request.form['channel_id'], 'channel_name': request.form['channel_name'], 'user_id': request.form['user_id'], 'user_name': request.form['user_name'], 'command': request.form['command'], 'text': request.form['text']}

    return 'you are authorized, and you said {text}! team_id:{team_id} team_domain:{team_domain} channel_id:{channel_id} channel_name:{channel_name} user_id:{user_id} user_name:{user_name} command:{command}'.format(**params), 200
