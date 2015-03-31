from flask import abort, current_app, request
from . import gloss as app
from . import db
from models import Definition, Interaction
from sqlalchemy import func, distinct
from re import sub, search, match
from requests import post
from datetime import datetime
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
    ''' Get a dict describing a standard webhook
    '''
    payload_values = {}
    payload_values['channel'] = channel_id
    payload_values['text'] = text
    payload_values['username'] = u'Gloss Bot'
    payload_values['icon_emoji'] = u':lipstick:'
    return payload_values

def send_webhook(channel_id=u'', text=None):
    ''' Send a standard webhook
    '''
    # don't send empty messages
    if not text:
        return

    # get the payload json
    payload_values = get_payload_values(channel_id=channel_id, text=text)
    payload = json.dumps(payload_values)
    # return the response
    return post(current_app.config['SLACK_WEBHOOK_URL'], data=payload)

def send_webhook_with_attachment(channel_id=u'', text=None, fallback=u'', pretext=u'', title=u'', color=u'#f33373', image_url=None):
    ''' Send a webhook with an attachment, for a more richly-formatted message.
        see https://api.slack.com/docs/attachments
    '''
    # don't send empty messages
    if not text:
        return

    # get the standard payload dict
    # :NOTE: sending text defined as 'pretext' to the standard payload and leaving
    #        'pretext' in the attachment empty. so that I can use markdown styling.
    payload_values = get_payload_values(channel_id=channel_id, text=pretext)
    # build the attachment dict
    attachment_values = {}
    attachment_values['fallback'] = fallback
    attachment_values['pretext'] = None
    attachment_values['title'] = title
    attachment_values['text'] = text
    attachment_values['color'] = color
    attachment_values['image_url'] = image_url
    # add the attachment dict to the payload and jsonify it
    payload_values['attachments'] = [attachment_values]
    payload = json.dumps(payload_values)

    # return the response
    return post(current_app.config['SLACK_WEBHOOK_URL'], data=payload)

def get_image_url(text):
    ''' Extract an image url from the passed text. If there are multiple image urls,
        only the first one will be returned.
    '''
    if 'http' not in text:
        return None

    for chunk in text.split(' '):
        if match('http', text) and search(r'[gif|jpg|jpeg|png|bmp]$', text):
            return chunk

    return None

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
            lines.append(u'{}{} {}'.format(u'{} '.format(prefix) if prefix else u'', period, singular if period == 1 else plural))
    # return the message
    return u'\n'.join(lines)

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
    full_text = sub(u' +', u' ', full_text)

    # was a command passed?
    command_components = full_text.split(' ')
    command_action = command_components[0]
    command_params = u' '.join(command_components[1:])

    # get the user name
    user_name = unicode(request.form['user_name'])

    #
    # commands that get private responses
    #

    if command_action == u'set':
        set_components = command_params.split('=')
        if len(set_components) != 2 or u'=' not in command_params:
            return u'Sorry, but *Gloss Bot* didn\'t understand your command. A set command should look like this: */gloss set EW = Eligibility Worker*', 200

        set_term = set_components[0].strip()
        set_value = set_components[1].strip()

        # check the database to see if the term's already defined
        entry = get_definition(set_term)
        if entry:
            if set_term != entry.term or set_value != entry.definition:
                # update the definition in the database
                last_term = entry.term
                last_value = entry.definition
                entry.term = set_term
                entry.definition = set_value
                entry.user = user_name
                entry.creation_date = datetime.utcnow()
                try:
                    db.session.add(entry)
                    db.session.commit()
                except Exception as e:
                    return u'Sorry, but *Gloss Bot* was unable to update that definition: {}, {}'.format(e.message, e.args), 200

                return u'*Gloss Bot* has set the definition for *{}* to *{}*, overwriting the previous entry, which was *{}* defined as *{}*'.format(set_term, set_value, last_term, last_value), 200

            else:
                return u'*Gloss Bot* already knows that the definition for *{}* is *{}*'.format(set_term, set_value), 200

        else:
            # save the definition in the database
            entry = Definition(term=set_term, definition=set_value, user=user_name)
            try:
                db.session.add(entry)
                db.session.commit()
            except Exception as e:
                return u'Sorry, but *Gloss Bot* was unable to save that definition: {}, {}'.format(e.message, e.args), 200

            return u'*Gloss Bot* has set the definition for *{}* to *{}*'.format(set_term, set_value), 200

    if command_action == u'delete':
        if not command_params or command_params == u' ':
            return u'Sorry, but *Gloss Bot* didn\'t understand your command. A delete command should look like this: */gloss delete EW*', 200

        delete_term = command_params

        # verify that the definition is in the database
        entry = get_definition(delete_term)
        if not entry:
            return u'Sorry, but *Gloss Bot* has no definition for *{}*'.format(delete_term), 200

        # delete the definition from the database
        try:
            db.session.delete(entry)
            db.session.commit()
        except Exception as e:
            return u'Sorry, but *Gloss Bot* was unable to delete that definition: {}, {}'.format(e.message, e.args), 200

        return u'*Gloss Bot* has deleted the definition for *{}*, which was *{}*'.format(delete_term, entry.definition), 200

    if command_action == u'help' or command_action == u'?' or full_text == u'' or full_text == u' ':
        return u'*/gloss <term>* to define <term>\n*/gloss set <term> = <definition>* to set the definition for a term\n*/gloss delete <term>* to delete the definition for a term\n*/gloss help* to see this message\n*/gloss stats* to get statistics about Gloss Bot operations', 200

    #
    # commands that get public responses
    #

    channel_id = unicode(request.form['channel_id'])

    if command_action == u'stats':
        # send the message
        stats_newline = u'I have {}'.format(get_stats())
        stats_comma = sub(u'\n', u', ', stats_newline)
        fallback = u'{} /gloss stats: {}'.format(user_name, stats_comma)
        pretext = u'*{}* /gloss stats'.format(user_name, full_text)
        title = u''
        send_webhook_with_attachment(channel_id=channel_id, text=stats_newline, fallback=fallback, pretext=pretext, title=title)
        return u'', 200

    # get the definition
    entry = get_definition(full_text)
    if not entry:
        # remember this query
        log_query(term=full_text, user=user_name, action=u'not_found')

        return u'Sorry, but *Gloss Bot* has no definition for *{term}*. You can set a definition with the command */gloss set {term} = <definition>*'.format(term=full_text), 200

    # remember this query
    log_query(term=full_text, user=user_name, action=u'found')

    image_url = get_image_url(entry.definition)
    fallback = u'{} /gloss {}: {}'.format(user_name, entry.term, entry.definition)
    pretext = u'*{}* /gloss {}'.format(user_name, full_text)
    title = entry.term
    text = entry.definition
    send_webhook_with_attachment(channel_id=channel_id, text=text, fallback=fallback, pretext=pretext, title=title, image_url=image_url)

    return u'', 200
