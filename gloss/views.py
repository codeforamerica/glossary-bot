from flask import abort, current_app, request
from . import gloss as app
from . import db
from models import Definition
from re import sub
from requests import post

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

def send_webhook(channel_id=u'', text=u''):
    # don't send empty messages
    if not text:
        return

    # build the payload json
    payload_template = '''{{"channel": "{channel_id}", "username": "{bot_name}", "text": "{text}", "icon_emoji": ":{icon_emoji}:"}}'''
    payload_values = {}
    payload_values['channel_id'] = channel_id
    payload_values['bot_name'] = u'Gloss Bot'
    payload_values['text'] = text
    payload_values['icon_emoji'] = u'lipstick'
    payload = payload_template.format(**payload_values)
    # return the response
    return post(current_app.config['SLACK_WEBHOOK_URL'], data=payload)

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    # strip excess spaces from the text
    full_text = unicode(request.form['text'].strip())
    full_text = sub(' +', ' ', full_text)

    # was a command passed?
    command_components = full_text.split(' ')
    command_action = command_components[0]
    command_params = ' '.join(command_components[1:])

    #
    # commands that get private responses
    #

    if command_action == u'set':
        set_components = command_params.split('=')
        if len(set_components) != 2 or u'=' not in command_params:
            return 'I\'m sorry, but I didn\'t understand your command. A set command should look like this: /gloss set EW = Eligibility Worker', 200

        set_term = set_components[0].strip()
        set_value = set_components[1].strip()
        return 'I think you want to set the definition for \'{}\' to \'{}\''.format(set_term, set_value), 200

    if command_action == u'delete':
        if not command_params or command_params == u' ':
            return 'I\'m sorry, but I didn\'t understand your command. A delete command should look like this: /gloss delete EW', 200

        delete_term = command_params
        return 'I think you want to delete the definition for \'{}\''.format(delete_term), 200

    if command_action == u'help' or full_text == u'' or full_text == u' ':
        return 'I think you want help using Glossary Bot!\n*/gloss <term>* _to define <term>_\n*/gloss set <term> = <definition>* _to set the definition for a term_\n*/gloss delete <term>* _to delete the definition for a term_\n*/gloss help* _to see this message_\n*/gloss stats* _to get statistics about my operations_', 200

    #
    # commands that get public responses
    #

    channel_id = unicode(request.form['channel_id'])

    if command_action == u'stats':
        msg_text = '{} wants statistics about my operations.'.format(request.form['user_name'])
        webhook_response = send_webhook(channel_id=channel_id, text=msg_text)
        return 'Response from the webhook to #{}/{}: {}/{}'.format(unicode(request.form['channel_name']), channel_id, webhook_response.status_code, webhook_response.content), 200

    msg_text = u'{} wants a definition for the term \'{}\''.format(request.form['user_name'], full_text)
    webhook_response = send_webhook(channel_id=channel_id, text=msg_text)
    return 'Response from the webhook to #{}/{}: {}/{}'.format(unicode(request.form['channel_name']), channel_id, webhook_response.status_code, webhook_response.content), 200

    # params = {'team_id': request.form['team_id'], 'team_domain': request.form['team_domain'], 'channel_id': request.form['channel_id'], 'channel_name': request.form['channel_name'], 'user_id': request.form['user_id'], 'user_name': request.form['user_name'], 'command': request.form['command'], 'text': request.form['text']}
    # return 'you are authorized, and you said {text}! team_id:{team_id} team_domain:{team_domain} channel_id:{channel_id} channel_name:{channel_name} user_id:{user_id} user_name:{user_name} command:{command}'.format(**params), 200
