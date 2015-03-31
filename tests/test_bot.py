#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
from httmock import response, HTTMock
from os import environ
from flask import current_app
from gloss import create_app, db
from gloss.models import Definition, Interaction

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

    def test_set_definition_with_lots_of_spaces(self):
        ''' Verify that excess whitespace is trimmed when parsing the set command.
        '''
        self.client.post('/', data={'token': u'meowser_token', 'text': u'     EW   =    Eligibility      Worker  ', 'user_name': u'glossie', 'channel_id': u'123456'})

        filter = Definition.term == u'EW'
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, u'EW')
        self.assertEqual(definition_check.definition, u'Eligibility Worker')

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








