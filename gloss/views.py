from flask import abort, current_app, request
from . import gloss as app
from . import db
from models import Definition, Interaction
from sqlalchemy import func, distinct
from re import compile, match, search, sub, UNICODE
from requests import post
from datetime import datetime
import json

STATS_CMDS = (u'stats',)
RECENT_CMDS = (u'learnings',)
HELP_CMDS = (u'help', u'?')
SET_CMDS = (u'=',)
DELETE_CMDS = (u'delete',)

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

def send_webhook_with_attachment(channel_id=u'', text=None, fallback=u'', pretext=u'', title=u'', color=u'#f33373', image_url=None, mrkdwn_in=[]):
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
    if len(mrkdwn_in):
        attachment_values['mrkdwn_in'] = mrkdwn_in
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
        if verify_image_url(text) and verify_url(text):
            return chunk

    return None

def verify_url(text):
    ''' verify that the passed text is a URL

        Adapted from @adamrofer's Python port of @dperini's pattern here: https://gist.github.com/dperini/729294
    '''
    url_pattern = compile(u'^(?:(?:https?)://|)(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)))(?::\d{2,5})?(?:/\S*)?$', UNICODE)
    return url_pattern.match(text)

def verify_image_url(text):
    ''' Verify that the passed text is an image URL.

        We're verifying image URLs for inclusion in Slack's Incoming Webhook integration, which
        requires a scheme at the beginning (http(s)) and a file extention at the end to render
        correctly. So, a URL which passes verify_url() (like example.com/kitten.gif) might not
        pass this test. If you need to test that the URL is both valid AND an image suitable for
        the Incoming Webhook integration, run it through both verify_url() and verify_image_url().
    '''
    return (match('http', text) and search(r'[gif|jpg|jpeg|png|bmp]$', text))

def get_stats():
    ''' Gather and return some statistics
    '''
    entries = db.session.query(func.count(Definition.term)).scalar()
    definers = db.session.query(func.count(distinct(Definition.user_name))).scalar()
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

def get_learnings(how_many=12, sort_order=u'recent', offset=0):
    ''' Gather and return some recent definitions
    '''
    order_func = Definition.creation_date.desc()
    prefix_singluar = u'I recently learned the definition for'
    prefix_plural = u'I recently learned definitions for'
    if sort_order == u'random':
        order_func = func.random()
        prefix_singluar = u'I know the definition for'
        prefix_plural = u'I know definitions for'

    # if how_many is 0, ignore offset and return all results
    if how_many == 0:
        definitions = db.session.query(Definition).order_by(order_func).all()
    else:
        definitions = db.session.query(Definition).order_by(order_func).limit(how_many).offset(offset).all()

    if not definitions:
        no_definitions_text = u'I haven\'t learned any definitions yet.'
        return no_definitions_text, no_definitions_text

    wording = prefix_plural if len(definitions) > 1 else prefix_singluar
    plain_text = u'{}: {}'.format(wording, ', '.join([item.term for item in definitions]))
    rich_text = u'{}: {}'.format(wording, ', '.join([u'*{}*'.format(item.term) for item in definitions]))
    return plain_text, rich_text

def parse_learnings_params(command_params):
    ''' Parse the passed learnings command params
    '''
    recent_args = {}
    # extract parameters
    params_list = command_params.split(' ')
    for param in params_list:
        if param == u'random':
            recent_args['sort_order'] = param
            continue
        if param == u'all':
            recent_args['how_many'] = 0
            continue
        try:
            passed_int = int(param)
            if 'how_many' not in recent_args:
                recent_args['how_many'] = passed_int
            elif 'offset' not in recent_args:
                recent_args['offset'] = passed_int
        except ValueError:
            continue

    return recent_args

def log_query(term, user_name, action):
    ''' Log a query into the interactions table
    '''
    try:
        db.session.add(Interaction(term=term, user_name=user_name, action=action))
        db.session.commit()
    except:
        pass

def query_definition(term):
    ''' Query the definition for a term from the database
    '''
    return Definition.query.filter(func.lower(Definition.term) == func.lower(term)).first()

def get_command_action_and_params(command_text):
    ''' Parse the passed string for a command action and parameters
    '''
    command_components = command_text.split(' ')
    command_action = command_components[0].lower()
    command_params = u' '.join(command_components[1:])
    return command_action, command_params

def query_definition_and_get_response(command_text, user_name, channel_id, private_response):
    ''' Get the definition for the passed term and return the appropriate responses
    '''
    # query the definition
    entry = query_definition(command_text)
    if not entry:
        # remember this query
        log_query(term=command_text, user_name=user_name, action=u'not_found')

        return u'Sorry, but *Gloss Bot* has no definition for *{term}*. You can set a definition with the command */gloss {term} = <definition>*'.format(term=command_text), 200

    # remember this query
    log_query(term=command_text, user_name=user_name, action=u'found')

    fallback = u'{} /gloss {}: {}'.format(user_name, entry.term, entry.definition)
    if not private_response:
        image_url = get_image_url(entry.definition)
        pretext = u'*{}* /gloss {}'.format(user_name, command_text)
        title = entry.term
        text = entry.definition
        send_webhook_with_attachment(channel_id=channel_id, text=text, fallback=fallback, pretext=pretext, title=title, image_url=image_url)
        return u'', 200
    else:
        return fallback, 200

def set_definition_and_get_response(command_params, user_name):
    ''' Set the definition for the passed parameters and return the approriate responses
    '''
    set_components = command_params.split('=', 1)
    set_term = set_components[0].strip()
    set_value = set_components[1].strip() if len(set_components) > 1 else u''

    # reject poorly formed set commands
    if u'=' not in command_params or not set_term or not set_value:
        return u'Sorry, but *Gloss Bot* didn\'t understand your command. You can set definitions like this: */gloss EW = Eligibility Worker*', 200

    # reject attempts to set reserved terms
    if set_term.lower() in STATS_CMDS + RECENT_CMDS + HELP_CMDS:
        return u'Sorry, but *Gloss Bot* can\'t set a definition for *{}* because it\'s a reserved term.'.format(set_term)

    # check the database to see if the term's already defined
    entry = query_definition(set_term)
    if entry:
        if set_term != entry.term or set_value != entry.definition:
            # update the definition in the database
            last_term = entry.term
            last_value = entry.definition
            entry.term = set_term
            entry.definition = set_value
            entry.user_name = user_name
            entry.creation_date = datetime.utcnow()
            try:
                db.session.add(entry)
                db.session.commit()
            except Exception as e:
                return u'Sorry, but *Gloss Bot* was unable to update that definition: {}, {}'.format(e.message, e.args), 200

            return u'*Gloss Bot* has set the definition for *{}* to *{}*, overwriting the previous entry, which was *{}* defined as *{}*'.format(set_term, set_value, last_term, last_value), 200

        else:
            return u'*Gloss Bot* already knows that the definition for *{}* is *{}*'.format(set_term, set_value), 200

    # save the definition in the database
    entry = Definition(term=set_term, definition=set_value, user_name=user_name)
    try:
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        return u'Sorry, but *Gloss Bot* was unable to save that definition: {}, {}'.format(e.message, e.args), 200

    return u'*Gloss Bot* has set the definition for *{}* to *{}*'.format(set_term, set_value), 200

#
# ROUTES
#

@app.route('/', methods=['POST'])
def index():
    # verify that the request is authorized
    if request.form['token'] != current_app.config['SLACK_TOKEN']:
        abort(401)

    # get the user name and channel ID
    user_name = unicode(request.form['user_name'])
    channel_id = unicode(request.form['channel_id'])

    # strip excess spaces from the text
    full_text = unicode(request.form['text'].strip())
    full_text = sub(u' +', u' ', full_text)
    command_text = full_text

    #
    # GET definition (for a single word that can't be interpreted as a command)
    #

    # if the text is a single word that's not a single-word command, treat it as a get
    if command_text.count(u' ') is 0 and len(command_text) > 0 and \
       command_text.lower() not in STATS_CMDS + RECENT_CMDS + HELP_CMDS + SET_CMDS:
        return query_definition_and_get_response(command_text, user_name, channel_id, False)

    #
    # SET definition
    #

    # if the text contains an '=', treat it as a 'set' command
    if '=' in command_text:
        return set_definition_and_get_response(command_text, user_name)

    # we'll respond privately if the text is prefixed with 'shh ' (or any number of s followed by any number of h)
    shh_pattern = compile(r'^s+h+ ')
    private_response = shh_pattern.match(command_text)
    if private_response:
        # strip the 'shh' from the command text
        command_text = shh_pattern.sub('', command_text)

    # extract the command action and parameters
    command_action, command_params = get_command_action_and_params(command_text)

    #
    # DELETE definition
    #

    if command_action in DELETE_CMDS:
        delete_term = command_params

        # verify that the definition is in the database
        entry = query_definition(delete_term)
        if not entry:
            return u'Sorry, but *Gloss Bot* has no definition for *{}*'.format(delete_term), 200

        # delete the definition from the database
        try:
            db.session.delete(entry)
            db.session.commit()
        except Exception as e:
            return u'Sorry, but *Gloss Bot* was unable to delete that definition: {}, {}'.format(e.message, e.args), 200

        return u'*Gloss Bot* has deleted the definition for *{}*, which was *{}*'.format(delete_term, entry.definition), 200

    #
    # HELP
    #

    if command_action in HELP_CMDS or command_text == u'' or command_text == u' ':
        return u'*/gloss <term>* to show the definition for a term\n*/gloss <term> = <definition>* to set the definition for a term\n*/gloss delete <term>* to delete the definition for a term\n*/gloss help* to see this message\n*/gloss stats* to show usage statistics\n*/gloss learnings* to show recently defined terms\n*/gloss shh <command>* to get a private response\n<https://github.com/codeforamerica/glossary-bot/issues|report bugs and request features>', 200

    #
    # STATS
    #

    if command_action in STATS_CMDS:
        stats_newline = u'I have {}'.format(get_stats())
        stats_comma = sub(u'\n', u', ', stats_newline)
        if not private_response:
            # send the message
            fallback = u'{} /gloss stats: {}'.format(user_name, stats_comma)
            pretext = u'*{}* /gloss stats'.format(user_name)
            title = u''
            send_webhook_with_attachment(channel_id=channel_id, text=stats_newline, fallback=fallback, pretext=pretext, title=title)
            return u'', 200

        else:
            return stats_comma, 200

    #
    # LEARNINGS/RECENT
    #

    if command_action in RECENT_CMDS:
        # extract parameters
        recent_args = parse_learnings_params(command_params)
        learnings_plain_text, learnings_rich_text = get_learnings(**recent_args)
        if not private_response:
            # send the message
            fallback = u'{} /gloss learnings {}: {}'.format(user_name, command_params, learnings_plain_text)
            pretext = u'*{}* /gloss learnings {}'.format(user_name, command_params)
            title = u''
            send_webhook_with_attachment(channel_id=channel_id, text=learnings_rich_text, fallback=fallback, pretext=pretext, title=title, mrkdwn_in=["text"])
            return u'', 200

        else:
            return learnings_plain_text, 200

    #
    # GET definition (for any text that wasn't caught before this)
    #

    # check the definition
    return query_definition_and_get_response(command_text, user_name, channel_id, private_response)
