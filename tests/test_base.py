#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
from os import environ
from gloss import create_app, db

class TestBase(unittest.TestCase):
    ''' A base class for bot tests.
    '''

    def setUp(self):
        environ['DATABASE_URL'] = 'postgresql:///glossary-bot-test'
        environ['SLACK_TOKEN'] = 'meowser_token'
        environ['SLACK_WEBHOOK_URL'] = 'http://hooks.example.com/services/HELLO/LOVELY/WORLD'

        self.app = create_app(environ)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.app.testing = True
        self.db = db
        self.client = self.app.test_client()

    def tearDown(self):
        self.db.session.close()
        self.db.drop_all()
        # drop_all doesn't drop the alembic_version table
        self.db.session.execute('DROP TABLE IF EXISTS alembic_version')
        self.db.session.commit()
        self.app_context.pop()

    def post_command(self, text, slash_command="/gloss"):
        return self.client.post('/', data={'token': "meowser_token", 'text': text, 'user_name': "glossie", 'channel_id': "123456", 'command': slash_command})
