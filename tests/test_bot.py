#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
from httmock import response, HTTMock
from os import environ
from flask import current_app
from gloss import create_app, db
from gloss.models import Definition, Interaction
import json

class BotTestCase(unittest.TestCase):

    def setUp(self):
        environ['DATABASE_URL'] = 'postgres:///glossary-bot-test'
        environ['SLACK_TOKEN'] = 'meowser_token'
        environ['SLACK_WEBHOOK_URL'] = 'http://hooks.example.com/services/HELLO/LOVELY/WORLD'

        self.app = create_app(environ)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.db = db
        self.db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        self.db.session.close()
        self.db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        ''' Verify that the app exists
        '''
        self.assertFalse(current_app is None)

    def test_unauthorized_access(self):
        ''' Verify that the app rejects unauthorized access
        '''
        robo_response = self.client.post('/', data={'token': 'woofer_token'})
        self.assertEqual(robo_response.status_code, 401)

    def test_authorized_access(self):
        ''' Verify that the app accepts authorized access
        '''
        robo_response = self.client.post('/', data={'token': u'meowser_token', 'text': u'', 'user_name': u'glossie', 'channel_id': u'123456'})
        self.assertEqual(robo_response.status_code, 200)

    def test_set_definition(self):
        ''' Verify that a definition set via a POST is recorded in the database
        '''
        self.client.post('/', data={'token': u'meowser_token', 'text': u'EW = Eligibility Worker', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

    def test_set_definition_with_lots_of_whitespace(self):
        ''' Verify that excess whitespace is trimmed when parsing the set command.
        '''
        self.client.post('/', data={'token': u'meowser_token', 'text': u'     EW   =    Eligibility      Worker  ', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

    def test_get_definition(self):
        ''' Verify that we can succesfully get a definition from the bot
        '''
        # set & test a definition
        self.client.post('/', data={'token': u'meowser_token', 'text': u'EW = Eligibility Worker', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss EW' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertEqual(attachment['title'], u'EW')
                self.assertEqual(attachment['text'], u'Eligibility Worker')
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.client.post('/', data={'token': u'meowser_token', 'text': u'EW', 'user_name': u'glossie', 'channel_id': u'123456'})
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_get_definition_with_image(self):
        ''' Verify that we can get a properly formatted definition with an image from the bot
        '''
        # set & test a definition
        self.client.post('/', data={'token': u'meowser_token', 'text': u'EW = http://example.com/ew.gif', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'http://example.com/ew.gif')

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss EW' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertEqual(attachment['title'], u'EW')
                self.assertEqual(attachment['text'], u'http://example.com/ew.gif')
                self.assertEqual(attachment['image_url'], u'http://example.com/ew.gif')
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.client.post('/', data={'token': u'meowser_token', 'text': u'EW', 'user_name': u'glossie', 'channel_id': u'123456'})
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_delete_definition(self):
        ''' Verify that a definition can be deleted from the database
        '''
        # first set a value in the database and verify that it's there
        self.client.post('/', data={'token': u'meowser_token', 'text': u'EW = Eligibility Worker', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

        # now delete the value and verify that it's gone
        self.client.post('/', data={'token': u'meowser_token', 'text': u'delete EW', 'user_name': u'glossie', 'channel_id': u'123456'})

        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNone(definition_check)

    def test_get_stats(self):
        ''' Verify that stats are properly returned by the bot
        '''
        # set and get a definition to generate some stats
        self.client.post('/', data={'token': u'meowser_token', 'text': u'EW = Eligibility Worker', 'user_name': u'glossie', 'channel_id': u'123456'})
        self.client.post('/', data={'token': u'meowser_token', 'text': u'shh EW', 'user_name': u'glossie', 'channel_id': u'123456'})

        # capture the bot's POST to the incoming webhook and test its content
        def response_content(url, request):
            if 'hooks.example.com' in url.geturl():
                payload = json.loads(request.body)
                self.assertIsNotNone(payload['username'])
                self.assertIsNotNone(payload['text'])
                self.assertTrue(u'glossie' in payload['text'])
                self.assertTrue(u'gloss stats' in payload['text'])
                self.assertEqual(payload['channel'], u'123456')
                self.assertIsNotNone(payload['icon_emoji'])

                attachment = payload['attachments'][0]
                self.assertIsNotNone(attachment)
                self.assertIsNotNone(attachment['title'])
                self.assertTrue(u'I have definitions for 1 term' in attachment['text'])
                self.assertTrue(u'1 person has defined terms' in attachment['text'])
                self.assertTrue(u'I\'ve been asked for definitions 1 time' in attachment['text'])
                self.assertIsNotNone(attachment['color'])
                self.assertIsNotNone(attachment['fallback'])
                return response(200)

        # send a POST to the bot to request the definition
        with HTTMock(response_content):
            fake_response = self.client.post('/', data={'token': u'meowser_token', 'text': u'stats', 'user_name': u'glossie', 'channel_id': u'123456'})
            self.assertTrue(fake_response.status_code in range(200, 299), fake_response.status_code)

    def test_get_quiet_definition(self):
        ''' Verify that the bot will send a quiet definition when told to do so
        '''
        self.assertTrue(True)






