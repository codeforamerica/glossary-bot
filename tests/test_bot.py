#!/usr/bin/env python
# -*- coding: utf8 -*-
import unittest
import json
import responses
from flask import current_app
from gloss.models import Definition, Interaction
from tests.test_base import TestBase

class TestBot(TestBase):

    def setUp(self):
        super(TestBot, self).setUp()
        self.db.create_all()

    def test_app_exists(self):
        ''' The app exists
        '''
        self.assertFalse(current_app is None)

    def test_unauthorized_access(self):
        ''' The app rejects unauthorized access
        '''
        robo_response = self.client.post('/', data={'token': 'woofer_token'})
        self.assertEqual(robo_response.status_code, 401)

    def test_authorized_access(self):
        ''' The app accepts authorized access
        '''
        robo_response = self.post_command(text="")
        self.assertEqual(robo_response.status_code, 200)

    def test_set_definition(self):
        ''' A definition set via a POST is recorded in the database
        '''
        robo_response = self.post_command(text="EW = Eligibility Worker")
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

    def test_set_definition_with_lots_of_whitespace(self):
        ''' Excess whitespace is trimmed when parsing the set command.
        '''
        robo_response = self.post_command(text="     EW   =    Eligibility      Worker  ")
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

    def test_set_definition_with_multiple_equals_signs(self):
        ''' A set with multiple equals signs considers all equals signs after
            the first to be part of the definition
        '''
        robo_response = self.post_command(text="EW = Eligibility Worker = Cool Person=Yeah")
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker = Cool Person=Yeah")

    def test_reset_definition(self):
        ''' Setting a definition for an existing term overwrites the original
        '''
        robo_response = self.post_command(text="EW = Eligibility Worker")
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

        robo_response = self.post_command(text="EW = Egg Weathervane")
        self.assertTrue("overwriting the previous entry".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Egg Weathervane")

    def test_set_same_word_with_different_capitalization(self):
        ''' We can't set different definitions for the same word by using different cases
        '''
        robo_response = self.post_command(text="lower case = NOT UPPER CASE")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "lower case"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "lower case")
        self.assertEqual(definition_check.definition, "NOT UPPER CASE")

        robo_response = self.post_command(text="LOWER CASE = really not upper case")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("overwriting the previous entry".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="shh lower case")
        self.assertTrue("LOWER CASE: really not upper case".encode('utf-8') in robo_response.data)

    def test_set_identical_definition(self):
        ''' Correct response for setting an identical definition for an existing term
        '''
        robo_response = self.post_command(text="EW = Eligibility Worker")
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

        robo_response = self.post_command(text="EW = Eligibility Worker")
        self.assertTrue("already knows that the definition for".encode('utf-8') in robo_response.data)

    def test_set_command_word_definitions(self):
        ''' We can successfully set definitions for unreserved command words.
        '''
        robo_response = self.post_command(text="SHH = Sonic Hedge Hog")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "SHH"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "SHH")
        self.assertEqual(definition_check.definition, "Sonic Hedge Hog")

        robo_response = self.post_command(text="SSH = Secure SHell")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "SSH"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "SSH")
        self.assertEqual(definition_check.definition, "Secure SHell")

        robo_response = self.post_command(text="Delete = Remove or Obliterate")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "Delete"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "Delete")
        self.assertEqual(definition_check.definition, "Remove or Obliterate")

        robo_response = self.post_command(text="help me = I'm in hell")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("has set the definition".encode('utf-8') in robo_response.data)

        filter = Definition.term == "help me"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "help me")
        self.assertEqual(definition_check.definition, "I'm in hell")

    def test_failed_set_command_word_definitions(self):
        ''' We can't successfully set definitions for reserved command words.
        '''
        robo_response = self.post_command(text="Stats = Statistics")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("because it's a reserved term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="help = aid")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("because it's a reserved term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="LeArNiNgS = recently")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("because it's a reserved term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="? = riddle me this")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("because it's a reserved term".encode('utf-8') in robo_response.data)

    @responses.activate
    def test_get_definition(self):
        ''' We can succesfully set and get a definition from the bot
        '''
        # set & test a definition
        self.post_command(text="EW = Eligibility Worker")

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="EW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss EW" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], "EW")
        self.assertEqual(attachment['text'], "Eligibility Worker")
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, "glossie")
        self.assertEqual(interaction_check.term, "EW")
        self.assertEqual(interaction_check.action, "found")

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_get_definition_with_special_characters(self):
        ''' We can succesfully set and get a definition with special characters from the bot
        '''
        # set & test a definition
        self.post_command(text="EW = ™¥∑ø∂∆∫")

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "™¥∑ø∂∆∫")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="EW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss EW" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], "EW")
        self.assertEqual(attachment['text'], "™¥∑ø∂∆∫")
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, "glossie")
        self.assertEqual(interaction_check.term, "EW")
        self.assertEqual(interaction_check.action, "found")

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    def test_request_nonexistent_definition(self):
        ''' Test requesting a non-existent definition
        '''
        # send a POST to the bot to request the definition
        robo_response = self.post_command(text="EW")
        self.assertTrue("has no definition for".encode('utf-8') in robo_response.data)

        # the request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, "glossie")
        self.assertEqual(interaction_check.term, "EW")
        self.assertEqual(interaction_check.action, "not_found")

    @responses.activate
    def test_get_definition_with_image(self):
        ''' We can get a properly formatted definition with an image from the bot
        '''
        # set & test a definition
        self.post_command(text="EW = http://example.com/ew.gif")

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "http://example.com/ew.gif")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="EW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss EW" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], "EW")
        self.assertEqual(attachment['text'], "http://example.com/ew.gif")
        self.assertEqual(attachment['image_url'], "http://example.com/ew.gif")
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_set_alias(self):
        ''' An alias can be set for a definition
        '''
        # set & test a definition and some aliases
        original_term = "Glossary Bot"
        first_alias = "Gloss Bot"
        second_alias = "Glossbot"
        definition = "A Slack bot that maintains a glossary of terms created by its users, and responds to requests with definitions."
        self.post_command(text="{original_term} = {definition}".format(**locals()))
        self.post_command(text="{first_alias} = see {original_term}".format(**locals()))
        self.post_command(text="{second_alias} = see also {original_term}".format(**locals()))

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        # ask for the original definition
        rsp = self.post_command(text=original_term)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], original_term)
        self.assertEqual(attachment['text'], definition)

        # ask for the first alias
        rsp = self.post_command(text=first_alias)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[1].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], original_term)
        self.assertEqual(attachment['text'], definition)

        # ask for the second alias
        rsp = self.post_command(text=second_alias)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[2].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment['title'], original_term)
        self.assertEqual(attachment['text'], definition)

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    def test_delete_definition(self):
        ''' A definition can be deleted from the database
        '''
        # first set a value in the database and verify that it's there
        self.post_command(text="EW = Eligibility Worker")

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

        # now delete the value and verify that it's gone
        robo_response = self.post_command(text="delete EW")
        self.assertTrue("has deleted the definition for".encode('utf-8') in robo_response.data)

        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNone(definition_check)

    @responses.activate
    def test_get_stats(self):
        ''' Stats are properly returned by the bot
        '''
        # set and get a definition to generate some stats
        self.post_command(text="EW = Eligibility Worker")
        self.post_command(text="shh EW")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="stats")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss stats" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNotNone(attachment['title'])
        self.assertTrue("I have definitions for 1 term" in attachment['text'])
        self.assertTrue("1 person has defined terms" in attachment['text'])
        self.assertTrue("I've been asked for definitions 1 time" in attachment['text'])
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_get_stats_on_empty_database(self):
        ''' A coherent message is returned when requesting stats on an empty database
        '''
        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="stats")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss stats" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNotNone(attachment['title'])
        self.assertTrue("I don't have any definitions" in attachment['text'])
        self.assertTrue("Nobody has defined terms" in attachment['text'])
        self.assertTrue("Nobody has asked me for definitions" in attachment['text'])
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_get_learnings(self):
        ''' Learnings are properly returned by the bot
        '''
        # set some values in the database
        letters = ["K", "L", "M", "N", "Ó", "P", "Q", "R", "S", "T", "U", "V"]
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="learnings")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['username'])
        self.assertIsNotNone(payload['text'])
        self.assertTrue("glossie" in payload['text'])
        self.assertTrue("gloss learnings" in payload['text'])
        self.assertEqual(payload['channel'], "123456")
        self.assertIsNotNone(payload['icon_emoji'])

        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNotNone(attachment['title'])

        self.assertTrue("I recently learned definitions for" in attachment['text'])
        self.assertTrue("KW" in attachment['text'])
        self.assertTrue("LW" in attachment['text'])
        self.assertTrue("MW" in attachment['text'])
        self.assertTrue("NW" in attachment['text'])
        self.assertTrue("ÓW" in attachment['text'])
        self.assertTrue("PW" in attachment['text'])
        self.assertTrue("QW" in attachment['text'])
        self.assertTrue("RW" in attachment['text'])
        self.assertTrue("SW" in attachment['text'])
        self.assertTrue("TW" in attachment['text'])
        self.assertTrue("UW" in attachment['text'])
        self.assertTrue("VW" in attachment['text'])
        self.assertIsNotNone(attachment['color'])
        self.assertIsNotNone(attachment['fallback'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    def test_random_learnings(self):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        # get chronological learnings
        robo_response = self.post_command(text="shh learnings")
        self.assertEqual(robo_response.status_code, 200)
        control = robo_response.data

        # get a few random learnings
        robo_response = self.post_command(text="shh learnings random")
        self.assertEqual(robo_response.status_code, 200)
        random1 = robo_response.data

        robo_response = self.post_command(text="shh learnings random")
        self.assertEqual(robo_response.status_code, 200)
        random2 = robo_response.data

        robo_response = self.post_command(text="shh learnings random")
        self.assertEqual(robo_response.status_code, 200)
        random3 = robo_response.data

        # if they're all equal, we've failed
        self.assertFalse(control == random1 and control == random2 and control == random3)

    def test_alphabetical_learnings(self):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = ["E", "G", "I", "K", "M", "O", "Q", "S", "R", "P", "N", "L", "J", "H", "F"]
        check = []
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))
            check.insert(0, "{}W".format(letter))

        desc_check = check[:12]
        alpha_check = list(check)
        alpha_check.sort()
        alpha_check = alpha_check[:12]

        # get chronological learnings
        robo_response = self.post_command(text="shh learnings")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(desc_check).encode('utf-8') in robo_response.data)

        # get alphabetical learnings
        robo_response = self.post_command(text="shh learnings alpha")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(alpha_check).encode('utf-8') in robo_response.data)

    def test_random_offset_learnings(self):
        ''' An offset group of learnings are returned randomized
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        # get chronological learnings
        robo_response = self.post_command(text="shh learnings 7 4")
        self.assertEqual(robo_response.status_code, 200)
        control = robo_response.data.decode()

        # get a list of the terms from the control string
        check_terms = control.split(', ')
        check_terms[0] = check_terms[0][-2:]

        # get a few random learnings
        robo_response = self.post_command(text="shh learnings random 7 4")
        self.assertEqual(robo_response.status_code, 200)
        random1 = robo_response.data

        robo_response = self.post_command(text="shh learnings random 7 4")
        self.assertEqual(robo_response.status_code, 200)
        random2 = robo_response.data

        robo_response = self.post_command(text="shh learnings random 7 4")
        self.assertEqual(robo_response.status_code, 200)
        random3 = robo_response.data

        # if they're all equal, we've failed
        self.assertFalse(control == random1 and control == random2 and control == random3)
        # but they should all have the same elements
        for term in check_terms:
            self.assertTrue(term.encode('utf-8') in random1)
            self.assertTrue(term.encode('utf-8') in random2)
            self.assertTrue(term.encode('utf-8') in random3)

    def test_all_learnings(self):
        ''' All learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        check = []
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))
            check.insert(0, "{}W".format(letter))

        # get all learnings
        robo_response = self.post_command(text="shh learnings all")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

        # if 'all' is part of the command, other limiting params are ignored
        robo_response = self.post_command(text="shh learnings all 5")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="shh learnings 5 3 all")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="shh learnings all 3 5")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

    def test_some_learnings(self):
        ''' Only a few learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        limit = 7
        check = ["{}W".format(item) for item in list(reversed(letters[-limit:]))]

        # get some learnings
        robo_response = self.post_command(text="shh learnings {}".format(limit))
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

    def test_offset_learnings(self):
        ''' An offset of learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        for letter in letters:
            self.post_command(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        limit = 7
        offset = 11
        check = ["{}W".format(item) for item in list(reversed(letters[-(limit + offset):-offset]))]

        # get some learnings
        robo_response = self.post_command(text="shh learnings {} {}".format(limit, offset))
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue(", ".join(check).encode('utf-8') in robo_response.data)

    def test_learnings_language(self):
        ''' Language describing learnings is numerically accurate
        '''
        # ask for recent definitions before any have been set
        robo_response = self.post_command(text="shh learnings")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I haven't learned any definitions yet.".encode('utf-8') in robo_response.data)

        # when one value has been set
        self.post_command(text="EW = Eligibility Worker")
        robo_response = self.post_command(text="shh learnings")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I recently learned the definition for".encode('utf-8') in robo_response.data)

        # when more than one value has been set
        self.post_command(text="FW = Fligibility Worker")
        robo_response = self.post_command(text="shh learnings")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I recently learned definitions for".encode('utf-8') in robo_response.data)

    def test_learnings_alternate_command(self):
        ''' Learnings are returned when sending the 'recent' command.
        '''
        # ask for recent definitions before any have been set
        robo_response = self.post_command(text="shh recent")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I haven't learned any definitions yet.".encode('utf-8') in robo_response.data)

        # when one value has been set
        self.post_command(text="EW = Eligibility Worker")
        robo_response = self.post_command(text="shh recent")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I recently learned the definition for".encode('utf-8') in robo_response.data)

        # when more than one value has been set
        self.post_command(text="FW = Fligibility Worker")
        robo_response = self.post_command(text="shh recent")
        self.assertEqual(robo_response.status_code, 200)
        self.assertTrue("I recently learned definitions for".encode('utf-8') in robo_response.data)

    def test_get_help(self):
        ''' Help is properly returned by the bot
        '''
        # testing different chunks of help text with each response
        robo_response = self.post_command(text="help")
        self.assertTrue("to show the definition for a term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="?")
        self.assertTrue("to set the definition for a term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="")
        self.assertTrue("to delete the definition for a term".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text=" ")
        self.assertTrue("to see this message".encode('utf-8') in robo_response.data)

    def test_custom_slash_command_for_private_requests(self):
        ''' A slash command other than /gloss is echoed in the bot's response
        '''
        test_command = "/gg"
        # the help command
        robo_response = self.post_command(text="help", slash_command=test_command)
        self.assertTrue("*{}".format(test_command).encode('utf-8') in robo_response.data)
        self.assertFalse("*/gloss".encode('utf-8') in robo_response.data)

        # ask for a definition that doesn't exist
        robo_response = self.post_command(text="shh EW", slash_command=test_command)
        self.assertTrue("*{}".format(test_command).encode('utf-8') in robo_response.data)
        self.assertFalse("*/gloss".encode('utf-8') in robo_response.data)

        # get a definition that does exist
        self.post_command(text="EW = Eligibility Worker", slash_command=test_command)
        robo_response = self.post_command(text="shh EW", slash_command=test_command)
        self.assertTrue("{}".format(test_command).encode('utf-8') in robo_response.data)
        self.assertFalse("/gloss".encode('utf-8') in robo_response.data)

        # get the error message for a bogus set
        robo_response = self.post_command(text="AW =", slash_command=test_command)
        self.assertTrue("*{}".format(test_command).encode('utf-8') in robo_response.data)
        self.assertFalse("*/gloss".encode('utf-8') in robo_response.data)

    @responses.activate
    def test_custom_slash_command_for_public_stats(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public stats request.
        '''
        test_command = "/gg"
        # set and get a definition to generate some stats
        self.post_command(text="EW = Eligibility Worker")
        self.post_command(text="shh EW")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="stats", slash_command=test_command)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['text'])
        self.assertTrue("{command} stats".format(command=test_command) in payload['text'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_custom_slash_command_for_public_definition(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public definition request.
        '''
        test_command = "/gg"
        # set and get a definition to generate some stats
        self.post_command(text="EW = Eligibility Worker")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="EW", slash_command=test_command)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['text'])
        self.assertTrue("{command} EW".format(command=test_command) in payload['text'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    @responses.activate
    def test_custom_slash_command_for_public_learnings(self):
        ''' A slash command other than /gloss is echoed in the bot's response
            to a public learnings request.
        '''
        test_command = "/gg"

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="learnings", slash_command=test_command)
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)

        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        self.assertIsNotNone(payload['text'])
        self.assertTrue("{command} learnings".format(command=test_command) in payload['text'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

    def test_get_quiet_definition(self):
        ''' The bot will send a quiet definition when told to do so
        '''
        # set & test a definition
        self.post_command(text="EW = Eligibility Worker")

        filter = Definition.term == "EW"
        definition_check = self.db.session.query(Definition).filter(filter).first()
        self.assertIsNotNone(definition_check)
        self.assertEqual(definition_check.term, "EW")
        self.assertEqual(definition_check.definition, "Eligibility Worker")

        # send a POST to the bot to request the quiet definition
        robo_response = self.post_command(text="shh EW")
        self.assertTrue("glossie".encode('utf-8') in robo_response.data)
        self.assertTrue("EW: Eligibility Worker".encode('utf-8') in robo_response.data)

        # send POSTs with variations of 'shh' to make sure that they're caught
        robo_response = self.post_command(text="ssh EW")
        self.assertTrue("glossie".encode('utf-8') in robo_response.data)
        self.assertTrue("EW: Eligibility Worker".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="sh EW")
        self.assertTrue("glossie".encode('utf-8') in robo_response.data)
        self.assertTrue("EW: Eligibility Worker".encode('utf-8') in robo_response.data)

        # at least one request was recorded in the interactions table
        interaction_check = self.db.session.query(Interaction).first()
        self.assertIsNotNone(interaction_check)
        self.assertEqual(interaction_check.user_name, "glossie")
        self.assertEqual(interaction_check.term, "EW")
        self.assertEqual(interaction_check.action, "found")

    def test_bad_set_commands(self):
        ''' We get the right error back when sending bad set commands
        '''
        robo_response = self.post_command(text="EW =")
        self.assertTrue("You can set definitions like this".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="=")
        self.assertTrue("You can set definitions like this".encode('utf-8') in robo_response.data)

        robo_response = self.post_command(text="= = =")
        self.assertTrue("You can set definitions like this".encode('utf-8') in robo_response.data)

    @responses.activate
    def test_bad_image_urls_rejected(self):
        ''' Bad image URLs are not sent in the attachment's image_url parameter
        '''
        # set some definitions with bad image URLs
        self.post_command(text="EW = http://kittens.gif")
        self.post_command(text="FW = httpdoggie.jpeg")
        self.post_command(text="GW = http://stupid/goldfish.bmp")
        self.post_command(text="HW = http://s.mlkshk-cdn.com/r/13ILU")

        # set a fake Slack webhook URL
        fake_webhook_url = 'http://webhook.example.com/'
        current_app.config['SLACK_WEBHOOK_URL'] = fake_webhook_url

        # create a mock to receive POST requests to that URL
        responses.add(responses.POST, fake_webhook_url, status=200)

        rsp = self.post_command(text="EW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)
        # test the captured post payload
        payload = json.loads(responses.calls[0].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNone(attachment['image_url'])

        rsp = self.post_command(text="FW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)
        # test the captured post payload
        payload = json.loads(responses.calls[1].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNone(attachment['image_url'])

        rsp = self.post_command(text="GW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)
        # test the captured post payload
        payload = json.loads(responses.calls[2].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNone(attachment['image_url'])

        rsp = self.post_command(text="HW")
        self.assertTrue(rsp.status_code in range(200, 299), rsp.status_code)
        # test the captured post payload
        payload = json.loads(responses.calls[3].request.body)
        attachment = payload['attachments'][0]
        self.assertIsNotNone(attachment)
        self.assertIsNone(attachment['image_url'])

        # delete the fake Slack webhook URL
        del(current_app.config['SLACK_WEBHOOK_URL'])
        # reset the mock
        responses.reset()

if __name__ == '__main__':
    unittest.main()
