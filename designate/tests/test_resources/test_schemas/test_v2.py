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
from designate.openstack.common import log as logging
from designate import schema
from designate.tests import TestCase

LOG = logging.getLogger(__name__)


class SchemasV2Test(TestCase):
    def test_recordset(self):
        validator = schema.Schema('v2', 'recordset')

        # Pass Expected
        validator.validate({
            'recordset': {
                'id': 'b22d09e0-efa3-11e2-b778-0800200c9a66',
                'zone_id': 'b22d09e0-efa3-11e2-b778-0800200c9a66',
                'name': 'example.com.',
                'type': 'A'
            }
        })

        # Pass Expected
        validator.validate({
            'recordset': {
                'id': 'b22d09e0-efa3-11e2-b778-0800200c9a66',
                'zone_id': 'b22d09e0-efa3-11e2-b778-0800200c9a66',
                'name': 'example.com.',
                'type': 'MX'
            }
        })
