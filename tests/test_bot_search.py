#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
import logging
import random
from flask_migrate import upgrade
from flask.ext.migrate import Migrate
from tests.test_base import TestBase

class TestBotSearch(TestBase):

    def setUp(self):
        super(TestBotSearch, self).setUp()
        # suppress logging
        logging.disable(logging.CRITICAL)
        # run the database migrations
        Migrate(self.app, self.db)
        upgrade()

    def tearDown(self):
        super(TestBotSearch, self).tearDown()
        logging.disable(logging.NOTSET)

    def test_suggestions_made_when_no_match_found(self):
        ''' When a definition is requested for a term that isn't in the database, a list
            of suggestions is returned.
        '''
        # set some definitions
        # this is the order the matches should be returned in
        matches = [
            (u'pastinkmy', u'a funky lunchmeat'),
            (u'stinked stink', u'a really bad smell'),
            (u'standard stink', u'a bad smell'),
            (u'foul odor', u'a stink that is really stinking up the room'),
            (u'stench', u'a prominent stink')
        ]
        # set the definitions in random order
        randomized_matches = list(matches)
        random.shuffle(randomized_matches)
        for post_match in randomized_matches:
            self.post_command(text=u'{} = {}'.format(post_match[0], post_match[1]))

        # request a definition that doesn't exist, but that will generate suggestions
        robo_response = self.post_command(text=u'shh stink')
        match_text = ', '.join(['*{}*'.format(item[0]) for item in matches])
        self.assertTrue(match_text in robo_response.data)

if __name__ == '__main__':
    unittest.main()
