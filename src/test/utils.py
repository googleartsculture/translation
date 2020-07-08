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

import logging
import unittest

# from google.appengine.ext import testbed, ndb
# from google.appengine.datastore import datastore_stub_util

logging.disable(logging.WARNING)  # ndb is noisy


class TestbedTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestbedTestCase, cls).setUpClass()

    def setUp(self):

        # self.testbed = testbed.Testbed()
        # self.testbed.activate()
        # self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        # self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        # self.testbed.init_memcache_stub()
        # self.testbed.init_user_stub()
        # self.testbed.init_mail_stub()
        # self.testbed.init_taskqueue_stub()
        # self.testbed.init_blobstore_stub()
        # self.testbed.init_app_identity_stub()
        # self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
        # self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        # self.testbed.setup_env(app_id='test-app')
        unittest.TestCase.setUp(self)

    def tearDown(self):
        # ndb.get_context().clear_cache()
        # self.testbed.get_stub('datastore_v3').Clear()
        # self.testbed.deactivate()
        unittest.TestCase.tearDown(self)


def strip_xssi_prefix(s):
    return s.replace(")]}',\n", '')
