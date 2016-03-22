# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
import mock
from mock import patch
from oslo_config import cfg
import oslo_messaging as messaging
from oslo_log import log as logging

from designate import exceptions
from designate import objects
from designate.central import service as central_service
from designate.mdns import rpcapi as mdns_api
from designate.tests.test_api.test_v2 import ApiV2TestCase


LOG = logging.getLogger(__name__)


class ApiV2ZonesTest(ApiV2TestCase):
    def setUp(self):
        super(ApiV2ZonesTest, self).setUp()

        # Create the default TLDs
        self.create_default_tlds()

    def test_create_zone(self):
        # Create a zone
        fixture = self.get_zone_fixture(fixture=0)
        response = self.client.post_json('/zones/', fixture)
        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('PENDING', response.json['status'])
        self.assertEqual('PRIMARY', response.json['type'])
        self.assertEqual([], response.json['masters'])
        self.assertIsNone(response.json['updated_at'])

        for k in fixture:
            self.assertEqual(fixture[k], response.json[k])

    def test_create_zone_no_type(self):
        # Create a zone
        fixture = self.get_zone_fixture(fixture=0)
        del fixture['type']

        response = self.client.post_json('/zones/', fixture)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('PENDING', response.json['status'])
        self.assertEqual('PRIMARY', response.json['type'])
        self.assertEqual([], response.json['masters'])
        self.assertIsNone(response.json['updated_at'])

        for k in fixture:
            self.assertEqual(fixture[k], response.json[k])

    def test_create_zone_validation(self):
        # NOTE: The schemas should be tested separately to the API. So we
        #       don't need to test every variation via the API itself.
        # Fetch a fixture
        fixture = self.get_zone_fixture(fixture=0)

        # Add a junk field to the body
        fixture['junk'] = 'Junk Field'

        # Ensure it fails with a 400
        body = fixture

        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_email_too_long(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture.update({'email': 'a' * 255 + '@abc.com'})
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_invalid_email(self):
        invalid_emails = [
            'org',
            'example.org',
            'bla.example.org',
            'org.',
            'example.org.',
            'bla.example.org.',
        ]
        fixture = self.get_zone_fixture(fixture=0)
        for email in invalid_emails:
            fixture.update({'email': email})
            body = fixture
            self._assert_exception('invalid_object', 400,
                                   self.client.post_json,
                                   '/zones', body)

    def test_create_zone_email_missing(self):
        fixture = self.get_zone_fixture(fixture=0)
        del fixture['email']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_ttl_less_than_zero(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['ttl'] = -1
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_ttl_is_zero(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['ttl'] = 0
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_ttl_is_greater_than_max(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['ttl'] = 2174483648
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_ttl_is_invalid(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['ttl'] = "!@?>"
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_ttl_is_not_required_field(self):
        fixture = self.get_zone_fixture(fixture=0)
        body = fixture
        response = self.client.post_json('/zones', body)
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

    def test_create_zone_description_too_long(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['description'] = "a" * 161
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_name_is_missing(self):
        fixture = self.get_zone_fixture(fixture=0)
        del fixture['name']
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_name_too_long(self):
        fixture = self.get_zone_fixture(fixture=0)
        fixture['name'] = 'x' * 255 + ".com"
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_body_validation(self):
        fixture = self.get_zone_fixture(fixture=0)
        # Add id to the body
        fixture['id'] = '2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'
        # Ensure it fails with a 400
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

        fixture = self.get_zone_fixture(fixture=0)
        # Add created_at to the body
        fixture['created_at'] = '2014-03-12T19:07:53.000000'
        # Ensure it fails with a 400
        body = fixture
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', body)

    def test_create_zone_invalid_name(self):
        # Try to create a zone with an invalid name
        fixture = self.get_zone_fixture(fixture=-1)

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones', fixture)

    @patch.object(central_service.Service, 'create_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_create_zone_timeout(self, _):
        fixture = self.get_zone_fixture(fixture=0)

        body = fixture

        self._assert_exception('timeout', 504, self.client.post_json,
                               '/zones/', body)

    @patch.object(central_service.Service, 'create_zone',
                  side_effect=exceptions.DuplicateZone())
    def test_create_zone_duplicate(self, _):
        fixture = self.get_zone_fixture(fixture=0)

        body = fixture

        self._assert_exception('duplicate_zone', 409, self.client.post_json,
                               '/zones/', body)

    def test_create_zone_missing_content_type(self):
        self._assert_exception('unsupported_content_type', 415,
                               self.client.post, '/zones')

    def test_create_zone_bad_content_type(self):
        self._assert_exception(
            'unsupported_content_type', 415, self.client.post, '/zones',
            headers={'Content-type': 'test/goat'})

    def test_zone_invalid_url(self):
        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980/invalid'
        self._assert_exception('not_found', 404, self.client.get, url,
                               headers={'Accept': 'application/json'})
        self._assert_exception('not_found', 404, self.client.patch_json, url)
        self._assert_exception('not_found', 404, self.client.delete, url)

        # Pecan returns a 405 for post
        response = self.client.post(url, status=405)
        self.assertEqual(405, response.status_int)

    def test_get_zones(self):
        response = self.client.get('/zones/')

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('zones', response.json)
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # We should start with 0 zones
        self.assertEqual(0, len(response.json['zones']))

        # We should start with 0 zones
        self.assertEqual(0, len(response.json['zones']))

        data = [self.create_zone(name='x-%s.com.' % i)
                for i in 'abcdefghij']
        self._assert_paging(data, '/zones', key='zones')

        self._assert_invalid_paging(data, '/zones', key='zones')

    @patch.object(central_service.Service, 'find_zones',
                  side_effect=messaging.MessagingTimeout())
    def test_get_zones_timeout(self, _):
        self._assert_exception('timeout', 504, self.client.get, '/zones/')

    def test_get_zone(self):
        # Create a zone
        zone = self.create_zone()

        response = self.client.get('/zones/%s' % zone['id'],
                                   headers=[('Accept', 'application/json')])

        # Check the headers are what we expect
        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('PENDING', response.json['status'])
        self.assertIsNone(response.json['updated_at'])
        self.assertEqual(zone['name'], response.json['name'])
        self.assertEqual(zone['email'], response.json['email'])

    def test_get_zone_invalid_id(self):
        self._assert_invalid_uuid(self.client.get, '/zones/%s')

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_get_zone_timeout(self, _):
        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'
        self._assert_exception('timeout', 504, self.client.get, url,
                               headers={'Accept': 'application/json'})

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=exceptions.ZoneNotFound())
    def test_get_zone_missing(self, _):
        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'
        self._assert_exception('zone_not_found', 404, self.client.get, url,
                               headers={'Accept': 'application/json'})

    def test_get_zone_bad_accept(self):
        url = '/zones/6e2146f3-87bc-4f47-adc5-4df0a5c78218'

        self.client.get(url, headers={'Accept': 'test/goat'}, status=406)

    def test_update_zone(self):
        # Create a zone
        zone = self.create_zone()

        # Prepare an update body
        body = {'email': 'prefix-%s' % zone['email']}

        response = self.client.patch_json('/zones/%s' % zone['id'], body,
                                          status=202)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])
        self.assertIn('status', response.json)

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual('prefix-%s' % zone['email'],
                         response.json['email'])

    def test_update_zone_invalid_id(self):
        self._assert_invalid_uuid(self.client.patch_json, '/zones/%s')

    def test_update_zone_validation(self):
        # NOTE: The schemas should be tested separatly to the API. So we
        #       don't need to test every variation via the API itself.
        # Create a zone
        zone = self.create_zone()

        # Prepare an update body with junk in the body
        body = {'email': 'prefix-%s' % zone['email'],
                'junk': 'Junk Field'}

        url = '/zones/%s' % zone['id']

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, body)

        # Prepare an update body with negative ttl in the body
        body = {'email': 'prefix-%s' % zone['email'],
                'ttl': -20}

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, body)

        # Prepare an update body with ttl > maximum (2147483647) in the body
        body = {'email': 'prefix-%s' % zone['email'],
                'ttl': 2147483648}

        # Ensure it fails with a 400
        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               url, body)

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=exceptions.DuplicateZone())
    def test_update_zone_duplicate(self, _):
        # Prepare an update body
        body = {'email': 'example@example.org'}

        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 409
        self._assert_exception('duplicate_zone', 409, self.client.patch_json,
                               url, body)

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_update_zone_timeout(self, _):
        # Prepare an update body
        body = {'email': 'example@example.org'}

        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 504
        self._assert_exception('timeout', 504, self.client.patch_json,
                               url, body)

    @patch.object(central_service.Service, 'get_zone',
                  side_effect=exceptions.ZoneNotFound())
    def test_update_zone_missing(self, _):
        # Prepare an update body
        body = {'email': 'example@example.org'}

        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        # Ensure it fails with a 404
        self._assert_exception('zone_not_found', 404, self.client.patch_json,
                               url, body)

    def test_delete_zone(self):
        zone = self.create_zone()

        response = self.client.delete('/zones/%s' % zone['id'], status=202)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual('DELETE', response.json['action'])
        self.assertEqual('PENDING', response.json['status'])

        # The deleted zone should still be listed
        zones = self.client.get('/zones/')
        self.assertEqual(1, len(zones.json['zones']))

    def test_delete_zone_invalid_id(self):
        self._assert_invalid_uuid(self.client.delete, '/zones/%s')

    @patch.object(central_service.Service, 'delete_zone',
                  side_effect=messaging.MessagingTimeout())
    def test_delete_zone_timeout(self, _):
        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        self._assert_exception('timeout', 504, self.client.delete, url)

    @patch.object(central_service.Service, 'delete_zone',
                  side_effect=exceptions.ZoneNotFound())
    def test_delete_zone_missing(self, _):
        url = '/zones/2fdadfb1-cf96-4259-ac6b-bb7b6d2ff980'

        self._assert_exception('zone_not_found', 404, self.client.delete,
                               url)

    def test_post_abandon_zone(self):
        zone = self.create_zone()
        url = '/zones/%s/tasks/abandon' % zone.id

        # Ensure that we get permission denied
        self._assert_exception('forbidden', 403, self.client.post_json, url)

        # Ensure that abandon zone succeeds with the right policy
        self.policy({'abandon_zone': '@'})
        response = self.client.post_json(url)
        self.assertEqual(204, response.status_int)

    def test_get_abandon_zone(self):
        zone = self.create_zone()
        url = '/zones/%s/tasks/abandon' % zone.id
        self._assert_exception('method_not_allowed', 405, self.client.get, url)

    def test_get_invalid_abandon(self):
        # This is an invalid endpoint - should return 404
        url = '/zones/tasks/abandon'
        self._assert_exception('not_found', 404, self.client.get, url)

    def test_get_zone_tasks(self):
        # This is an invalid endpoint - should return 404
        zone = self.create_zone()
        url = '/zones/%s/tasks' % zone.id
        self._assert_exception('not_found', 404, self.client.get, url)

    def test_create_secondary(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['masters'] = ["10.0.0.1"]

        response = self.client.post_json('/zones/', fixture)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIn('created_at', response.json)
        self.assertEqual('PENDING', response.json['status'])
        self.assertEqual(cfg.CONF['service:central'].managed_resource_email,
                         response.json['email'])

        self.assertIsNone(response.json['updated_at'])
        # Zone is not transferred yet
        self.assertIsNone(response.json['transferred_at'])
        # Serial defaults to 1
        self.assertEqual(response.json['serial'], 1)

        for k in fixture:
            self.assertEqual(fixture[k], response.json[k])

    def test_create_secondary_no_masters(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)

        self._assert_exception('invalid_object', 400, self.client.post_json,
                               '/zones/', fixture)

    def test_update_secondary(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)

        zone = objects.Zone(**fixture)
        zone.email = cfg.CONF['service:central'].managed_resource_email

        # Create a zone
        zone = self.central_service.create_zone(self.admin_context, zone)

        masters = ['10.0.0.1', '10.0.0.2']

        # Prepare an update body
        body = {'masters': masters}

        response = self.client.patch_json('/zones/%s' % zone['id'], body,
                                          status=202)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)

        # Check the body structure is what we expect
        self.assertIn('links', response.json)
        self.assertIn('self', response.json['links'])
        self.assertIn('status', response.json)

        # Check the values returned are what we expect
        self.assertIn('id', response.json)
        self.assertIsNotNone(response.json['updated_at'])
        self.assertEqual(masters, response.json['masters'])
        self.assertEqual(1, response.json['serial'])

    def test_xfr_request(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email
        fixture['masters'] = [{"host": "10.0.0.10", "port": 53}]

        # Create a zone
        zone = self.create_zone(**fixture)

        mdns = mock.Mock()
        with mock.patch.object(mdns_api.MdnsAPI, 'get_instance') as get_mdns:
            get_mdns.return_value = mdns
            mdns.get_serial_number.return_value = ('SUCCESS', 10, 1, )

            response = self.client.post_json(
                '/zones/%s/tasks/xfr' % zone['id'],
                None, status=202)

        self.assertTrue(mdns.perform_zone_xfr.called)

        # Check the headers are what we expect
        self.assertEqual(202, response.status_int)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual('""', response.body)

    def test_invalid_xfr_request(self):
        # Create a zone
        zone = self.create_zone()

        response = self.client.post_json(
            '/zones/%s/tasks/xfr' % zone['id'],
            None, status=400)

        # Check the headers are what we expect
        self.assertEqual(400, response.status_int)
        self.assertEqual('application/json', response.content_type)

    def test_update_secondary_email_invalid_object(self):
        # Create a zone
        fixture = self.get_zone_fixture('SECONDARY', 0)
        fixture['email'] = cfg.CONF['service:central'].managed_resource_email

        # Create a zone
        zone = self.create_zone(**fixture)

        body = {'email': 'foo@bar.io'}

        self._assert_exception('invalid_object', 400, self.client.patch_json,
                               '/zones/%s' % zone['id'], body)

    # Metadata tests
    def test_metadata_exists(self):
        response = self.client.get('/zones/')

        # Make sure the fields exist
        self.assertIn('metadata', response.json)
        self.assertIn('total_count', response.json['metadata'])

    def test_total_count(self):
        response = self.client.get('/zones/')

        # There are no zones by default
        self.assertEqual(0, response.json['metadata']['total_count'])

        # Create a zone
        fixture = self.get_zone_fixture(fixture=0)
        response = self.client.post_json('/zones/', fixture)

        response = self.client.get('/zones/')

        # Make sure total_count picked it up
        self.assertEqual(1, response.json['metadata']['total_count'])

    def test_total_count_pagination(self):
        # Create two zones
        fixture = self.get_zone_fixture(fixture=0)
        response = self.client.post_json('/zones/', fixture)

        fixture = self.get_zone_fixture(fixture=1)
        response = self.client.post_json('/zones/', fixture)

        # Paginate so that there is only one zone returned
        response = self.client.get('/zones?limit=1')

        self.assertEqual(1, len(response.json['zones']))

        # The total_count should know there are two
        self.assertEqual(2, response.json['metadata']['total_count'])

    def test_no_update_deleting(self):
        # Create a zone
        zone = self.create_zone()

        # Prepare an update body
        body = {'zone': {'email': 'prefix-%s' % zone['email']}}

        self.client.delete('/zones/%s' % zone['id'], status=202)
        self._assert_exception('bad_request', 400, self.client.patch_json,
                               '/zones/%s' % zone['id'], body)

    def test_get_nameservers(self):
        # Create a zone
        zone = self.create_zone()

        # Prepare an update body

        response = self.client.get('/zones/%s/nameservers' % zone['id'],
                                   headers=[('Accept', 'application/json')])

        self.assertIn('nameservers', response.json)
        self.assertEqual(1, len(response.json['nameservers']))
        self.assertIn('hostname', response.json['nameservers'][0])
        self.assertIn('priority', response.json['nameservers'][0])

    def test_get_zones_filter(self):
        # Add zones for testing
        fixtures = [
            self.get_zone_fixture(
                'PRIMARY', fixture=0, values={
                    'ttl': 3600,
                    'description': 'test1'
                }
            ),
            self.get_zone_fixture(
                'PRIMARY', fixture=1, values={
                    'ttl': 4000,
                    'description': 'test2'
                }
            )
        ]

        for fixture in fixtures:
            response = self.client.post_json('/zones/', fixture)

        get_urls = [
            # Filter by Type
            '/zones?type=%s' % fixtures[0]['type'],

            # Filter by Name
            '/zones?name=%s' % fixtures[0]['name'],

            # Filter by Email
            '/zones?email=example*',
            '/zones?email=%s' % fixtures[1]['email'],

            # Filter by TTL
            '/zones?ttl=3600',

            # Filter by Description
            '/zones?description=test1',
            '/zones?description=test*'
        ]

        correct_results = [2, 1, 2, 1, 1, 1, 2]

        for get_url, correct_result in zip(get_urls, correct_results):

            response = self.client.get(get_url)

            # Check the headers are what we expect
            self.assertEqual(200, response.status_int)
            self.assertEqual('application/json', response.content_type)

            # Check that the correct number of zones match
            self.assertEqual(correct_result, len(response.json['zones']))

    def test_invalid_zones_filter(self):
        invalid_url = '/zones?id=155477ef-e6c5-4b94-984d-8fc68c0c1a14'
        self._assert_exception(
            'bad_request', 400, self.client.get, invalid_url)
