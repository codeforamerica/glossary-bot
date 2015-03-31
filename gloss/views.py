from flask import abort, current_app, request
from . import gloss as app
from . import db
from models import Definition, Interaction
from sqlalchemy import func, distinct
from re import sub
from requests import post
import json

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

def get_payload_values(channel_id=u'', text=None):
    payload_values = {}
    payload_values['channel'] = channel_id
    payload_values['text'] = text
    payload_values['username'] = u'Gloss Bot'
    payload_values['icon_emoji'] = u':lipstick:'
    return payload_values

def send_webhook(channel_id=u'', text=None):
    # don't send empty messages
    if not text:
        return

    # get the payload json
    payload_values = get_payload_values(channel_id=channel_id, text=text)
    payload = json.dumps(payload_values)
    # return the response
    return post(current_app.config['SLACK_WEBHOOK_URL'], data=payload)

def send_webhook_with_attachment(channel_id=u'', text=None, fallback=u'', pretext=u'', title=u'', color=u'#df3333'):
    # don't send empty messages
    if not text:
        return

    # get the standard payload dict
    payload_values = get_payload_values(channel_id=channel_id)
    # build the attachment dict
    attachment_values = {}
    attachment_values['fallback'] = fallback
    attachment_values['pretext'] = pretext
    attachment_values['title'] = title
    attachment_values['text'] = text
    attachment_values['color'] = color
    # add the attachment dict to the payload and jsonify it
    payload_values['attachments'] = [attachment_values]
    payload = json.dumps(payload_values)

    # return the response
    return post(current_app.config['SLACK_WEBHOOK_URL'], data=payload)

def get_stats():
    ''' Gather and return some statistics
    '''
    entries = db.session.query(func.count(Definition.term)).scalar()
    definers = db.session.query(func.count(distinct(Definition.user))).scalar()
    queries = db.session.query(func.count(Interaction.action)).scalar()
    outputs = (
        (u'definitions for', entries, u'term', u'terms'),
        (u'', definers, u'person has defined terms', u'people have defined terms'),
        (u'I\'ve been asked for definitions', queries, u'time', u'times')
    )
    lines = []
    for prefix, period, singular, plural in outputs:
        if period:
            lines.append('{}{} {}'.format('{} '.format(prefix) if prefix else u'', period, singular if period == 1 else plural))
    # return the message
    return '\n'.join(lines)

def log_query(term, user, action):
    ''' Log a query into the interactions table
    '''
    try:
        db.session.add(Interaction(term=term, user=user, action=action))
        db.session.commit()
    except:
        pass

def get_definition(term):
    ''' Get the definition for a term from the database
    '''
    return Definition.query.filter(func.lower(Definition.term) == func.lower(term)).first()

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

    # get the user name
    user_name = unicode(request.form['user_name'])

    #
    # commands that get private responses
    #

    if command_action == u'set':
        set_components = command_params.split('=')
        if len(set_components) != 2 or u'=' not in command_params:
            return 'Sorry, but *Gloss Bot* didn\'t understand your command. A set command should look like this: */gloss set EW = Eligibility Worker*', 200

        set_term = set_components[0].strip()
        set_value = set_components[1].strip()

        # check the database to see if the term's already defined
        entry = get_definition(set_term)
        if entry:
            return 'Sorry, but *Gloss Bot* has already defined *{}* as *{}*'.format(set_term, entry.definition), 200

        # save the definition in the database
        entry = Definition(term=set_term, definition=set_value, user=user_name)
        try:
            db.session.add(entry)
            db.session.commit()
        except Exception as e:
            return 'Sorry, but *Gloss Bot* was unable to save that definition: {}, {}'.format(e.message, e.args), 200

        return '*Gloss Bot* has set the definition for *{}* to *{}*'.format(set_term, set_value), 200

    if command_action == u'delete':
        if not command_params or command_params == u' ':
            return 'Sorry, but *Gloss Bot* didn\'t understand your command. A delete command should look like this: */gloss delete EW*', 200

        delete_term = command_params

        # verify that the definition is in the database
        entry = get_definition(delete_term)
        if not entry:
            return 'Sorry, but *Gloss Bot* has no definition for *{}*'.format(delete_term), 200

        # delete the definition from the database
        try:
            db.session.delete(entry)
            db.session.commit()
        except Exception as e:
            return 'Sorry, but *Gloss Bot* was unable to delete that definition: {}, {}'.format(e.message, e.args), 200

        return '*Gloss Bot* has deleted the definition for *{}*, which was *{}*'.format(delete_term, entry.definition), 200

    if command_action == u'help' or command_action == u'?' or full_text == u'' or full_text == u' ':
        return '*/gloss <term>* to define <term>\n*/gloss set <term> = <definition>* to set the definition for a term\n*/gloss delete <term>* to delete the definition for a term\n*/gloss help* to see this message\n*/gloss stats* to get statistics about Gloss Bot operations', 200

    #
    # commands that get public responses
    #

    channel_id = unicode(request.form['channel_id'])

    if command_action == u'stats':
        # send the message
        msg_text = 'Since you asked, {}, I have {}.'.format(user_name, get_stats())
        webhook_response = send_webhook(channel_id=channel_id, text=msg_text)
        return u'', 200
        # return '(debug) Response from the webhook to #{}/{}: {}/{}'.format(unicode(request.form['channel_name']), channel_id, webhook_response.status_code, webhook_response.content), 200

    # get the definition
    entry = get_definition(full_text)
    if not entry:
        # remember this query
        log_query(term=full_text, user=user_name, action=u'not_found')

        return 'Sorry, but *Gloss Bot* has no definition for *{term}*. You can set a definition with the command */gloss set {term} = <definition>*'.format(term=full_text), 200

    # remember this query
    log_query(term=full_text, user=user_name, action=u'found')

    msg_text = u'*{}*: {}'.format(entry.term, entry.definition)
    fallback = '{} /gloss {}: {}'.format(user_name, entry.term, entry.definition)
    pretext = '{} /gloss {}'.format(user_name, full_text)
    title = entry.term
    text = entry.definition
    # send_webhook_with_attachment(channel_id=u'', text=None, fallback=u'', pretext=u'', title=u'', color=u'#df3333'):
    webhook_response = send_webhook_with_attachment(channel_id=channel_id, text=text, fallback=fallback, pretext=pretext, title=title)
    # webhook_response = send_webhook(channel_id=channel_id, text=msg_text)
    return u'', 200
    # return '(debug) Response from the webhook to #{}/{}: {}/{}'.format(unicode(request.form['channel_name']), channel_id, webhook_response.status_code, webhook_response.content), 200
