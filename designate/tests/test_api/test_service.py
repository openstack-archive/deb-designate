# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from designate.tests.test_api import ApiTestCase
from designate.api import service


class ApiServiceTest(ApiTestCase):
    def setUp(self):
        super(ApiServiceTest, self).setUp()

        # Use a random port for the API
        self.config(api_port=0, group='service:api')

        self.service = service.Service()

    def test_start_and_stop(self):
        # NOTE: Start is already done by the fixture in start_service()
        self.service.start()
        self.service.stop()
