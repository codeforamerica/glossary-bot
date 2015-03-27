from flask import abort, current_app, request
from . import gloss as app
from . import db
from models import Definition

'''
values posted by Slack:
    token: the authenticaton token from Slack; available in the integration settings.
    team_domain: the name of the team (i.e. what shows up in the URL: {xxx}.slack.com)
    team_id: unique ID for the team
    channel_name: the name of the channel the message was sent from
    channel_id: unique ID for the channel the message was sent from
    user_name: the name of the user that sent the message
    user_id: unique ID for the user that sent the message
    command: the command that was used to generate the request (like '/gloss')
    text: the text that was sent along with the command (like everything after '/gloss ')
'''

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    params = {'team_id': request.form['team_id'], 'team_domain': request.form['team_domain'], 'channel_id': request.form['channel_id'], 'channel_name': request.form['channel_name'], 'user_id': request.form['user_id'], 'user_name': request.form['user_name'], 'command': request.form['command'], 'text': request.form['text']}

    return 'you are authorized, and you said {text}! team_id:{team_id} team_domain:{team_domain} channel_id:{channel_id} channel_name:{channel_name} user_id:{user_id} user_name:{user_name} command:{command}'.format(**params), 200
