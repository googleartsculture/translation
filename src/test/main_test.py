#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from test.utils import TestbedTestCase

import main

class MainTests(TestbedTestCase):
    def setUp(self):
        super(MainTests, self).setUp()
        self.app = main.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_corpus_loaded(self):
        pass

    def test_text_items_loaded(self):
        pass

    def test_request_to_unknown_url(self):
        response = self.client.get('/unknown')
        self.assertEqual('404 NOT FOUND', response.status)
        data = json.loads(response.data)
        self.assertFalse(data.get('success'))
        self.assertEqual(404, data.get('code'))
        # We don't really care what the message says,
        # as long as it was a 404 status

    def test_translation_request_with_incorrect_http_method(self):
        response = self.client.get('/translation')
        self.assertEqual('405 METHOD NOT ALLOWED', response.status)
        data = json.loads(response.data)
        self.assertFalse(data.get('success'))
        self.assertEqual(405, data.get('code'))
        # We don't really care what the message says,
        # as long as it was a 405 status

    def test_translation_request_with_empty_payload(self):
        response = self.client.post('/translation', headers={}, json={})
        self.assertEqual('400 BAD REQUEST', response.status)
        data = json.loads(response.data)
        self.assertFalse(data.get('success'))
        self.assertEqual(400, data.get('code'))
        self.assertEqual('The request is missing the sequence parameter',
                            data.get('message'))

    def test_valid_translation_requests(self):
        response = self.client.post('/translation', json={'sequence': ['N1']})
        data = json.loads(response.data)
        self.assertEqual('200 OK', response.status)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertEqual(200, data.get('code'))
        self.assertIsInstance(data.get('result'), list)
        for item in data.get('result'):
            self.assertIsInstance(item, dict)
            self.assertIn('start', item)
            self.assertIsInstance(item.get('start'), int)
            self.assertIn('end', item)
            self.assertIsInstance(item.get('end'), int)
            self.assertIn('sequence', item)
            self.assertIsInstance(item.get('sequence'), list)
            for s in item.get('sequence'):
                self.assertIsInstance(s, str)

            self.assertIn('translations', item)
            self.assertIsInstance(item.get('translations'), list)
            for t in item.get('translations'):
                self.assertIsInstance(t, dict)
                self.assertIn('locale', t)
                self.assertIn('translation', t)

            self.assertIn('transliteration', item)
            self.assertIsInstance(item.get('transliteration'), str)

    def test_warmup_request_responds_200(self):
        """
        Asserts that a reuqest to /_ah/warmup is handled.
        """
        response = self.client.get('/_ah/warmup')
        self.assertEqual('200 OK', response.status)
