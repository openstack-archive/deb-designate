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
import uuid
import math

import testtools

from designate.openstack.common import log as logging
from designate import exceptions
from designate import objects
from designate.storage.base import Storage as StorageBase


LOG = logging.getLogger(__name__)


class StorageTestCase(object):
    def create_quota(self, **kwargs):
        """
        This create method has been kept in the StorageTestCase class as quotas
        are treated differently to other resources in Central.
        """

        context = kwargs.pop('context', self.admin_context)
        fixture = kwargs.pop('fixture', 0)

        values = self.get_quota_fixture(fixture=fixture, values=kwargs)

        if 'tenant_id' not in values:
            values['tenant_id'] = context.tenant

        return self.storage.create_quota(context, values)

    # Paging Tests
    def _ensure_paging(self, data, method):
        """
        Given an array of created items we iterate through them making sure
        they match up to things returned by paged results.
        """
        results = None
        item_number = 0

        for current_page in range(0, int(math.ceil(float(len(data)) / 2))):
            LOG.debug('Validating results on page %d', current_page)

            if results is not None:
                results = method(
                    self.admin_context, limit=2, marker=results[-1]['id'])
            else:
                results = method(self.admin_context, limit=2)

            LOG.critical('Results: %d', len(results))

            for result_number, result in enumerate(results):
                LOG.debug('Validating result %d on page %d', result_number,
                          current_page)
                self.assertEqual(
                    data[item_number]['id'], results[result_number]['id'])

                item_number += 1

    def test_paging_marker_not_found(self):
        with testtools.ExpectedException(exceptions.MarkerNotFound):
            self.storage.find_servers(
                self.admin_context, marker=str(uuid.uuid4()), limit=5)

    def test_paging_marker_invalid(self):
        with testtools.ExpectedException(exceptions.InvalidMarker):
            self.storage.find_servers(
                self.admin_context, marker='4')

    def test_paging_limit_invalid(self):
        with testtools.ExpectedException(exceptions.ValueError):
            self.storage.find_servers(
                self.admin_context, limit='z')

    def test_paging_sort_dir_invalid(self):
        with testtools.ExpectedException(exceptions.ValueError):
            self.storage.find_servers(
                self.admin_context, sort_dir='invalid_sort_dir')

    def test_paging_sort_key_invalid(self):
        with testtools.ExpectedException(exceptions.InvalidSortKey):
            self.storage.find_servers(
                self.admin_context, sort_key='invalid_sort_key')

    # Interface Tests
    def test_interface(self):
        self._ensure_interface(StorageBase, self.storage.__class__)

    # Quota Tests
    def test_create_quota(self):
        values = self.get_quota_fixture()
        values['tenant_id'] = self.admin_context.tenant

        result = self.storage.create_quota(self.admin_context, values)

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['resource'], values['resource'])
        self.assertEqual(result['hard_limit'], values['hard_limit'])

    def test_create_quota_duplicate(self):
        # Create the initial quota
        self.create_quota()

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.create_quota()

    def test_find_quotas(self):
        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single quota
        quota_one = self.create_quota()

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(quota_one['tenant_id'], actual[0]['tenant_id'])
        self.assertEqual(quota_one['resource'], actual[0]['resource'])
        self.assertEqual(quota_one['hard_limit'], actual[0]['hard_limit'])

        # Create a second quota
        quota_two = self.create_quota(fixture=1)

        actual = self.storage.find_quotas(self.admin_context)
        self.assertEqual(2, len(actual))

        self.assertEqual(quota_two['tenant_id'], actual[1]['tenant_id'])
        self.assertEqual(quota_two['resource'], actual[1]['resource'])
        self.assertEqual(quota_two['hard_limit'], actual[1]['hard_limit'])

    def test_find_quotas_criterion(self):
        quota_one = self.create_quota()
        quota_two = self.create_quota(fixture=1)

        criterion = dict(
            tenant_id=quota_one['tenant_id'],
            resource=quota_one['resource']
        )

        results = self.storage.find_quotas(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['tenant_id'], quota_one['tenant_id'])
        self.assertEqual(results[0]['resource'], quota_one['resource'])
        self.assertEqual(results[0]['hard_limit'], quota_one['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        results = self.storage.find_quotas(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['tenant_id'], quota_two['tenant_id'])
        self.assertEqual(results[0]['resource'], quota_two['resource'])
        self.assertEqual(results[0]['hard_limit'], quota_two['hard_limit'])

    def test_get_quota(self):
        # Create a quota
        expected = self.create_quota()
        actual = self.storage.get_quota(self.admin_context, expected['id'])

        self.assertEqual(actual['tenant_id'], expected['tenant_id'])
        self.assertEqual(actual['resource'], expected['resource'])
        self.assertEqual(actual['hard_limit'], expected['hard_limit'])

    def test_get_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_quota(self.admin_context, uuid)

    def test_find_quota_criterion(self):
        quota_one = self.create_quota()
        quota_two = self.create_quota(fixture=1)

        criterion = dict(
            tenant_id=quota_one['tenant_id'],
            resource=quota_one['resource']
        )

        result = self.storage.find_quota(self.admin_context, criterion)

        self.assertEqual(result['tenant_id'], quota_one['tenant_id'])
        self.assertEqual(result['resource'], quota_one['resource'])
        self.assertEqual(result['hard_limit'], quota_one['hard_limit'])

        criterion = dict(
            tenant_id=quota_two['tenant_id'],
            resource=quota_two['resource']
        )

        result = self.storage.find_quota(self.admin_context, criterion)

        self.assertEqual(result['tenant_id'], quota_two['tenant_id'])
        self.assertEqual(result['resource'], quota_two['resource'])
        self.assertEqual(result['hard_limit'], quota_two['hard_limit'])

    def test_find_quota_criterion_missing(self):
        expected = self.create_quota()

        criterion = dict(
            tenant_id=expected['tenant_id'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.find_quota(self.admin_context, criterion)

    def test_update_quota(self):
        # Create a quota
        quota = self.create_quota(fixture=1)

        # Update the Object
        quota.hard_limit = 5000

        # Perform the update
        quota = self.storage.update_quota(self.admin_context, quota)

        # Ensure the new value took
        self.assertEqual(5000, quota.hard_limit)

    def test_update_quota_duplicate(self):
        # Create two quotas
        quota_one = self.create_quota(fixture=0)
        quota_two = self.create_quota(fixture=1)

        # Update the Q2 object to be a duplicate of Q1
        quota_two.resource = quota_one.resource

        with testtools.ExpectedException(exceptions.DuplicateQuota):
            self.storage.update_quota(self.admin_context, quota_two)

    def test_update_quota_missing(self):
        quota = objects.Quota(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.update_quota(self.admin_context, quota)

    def test_delete_quota(self):
        quota = self.create_quota()

        self.storage.delete_quota(self.admin_context, quota['id'])

        with testtools.ExpectedException(exceptions.QuotaNotFound):
            self.storage.get_quota(self.admin_context, quota['id'])

    def test_delete_quota_missing(self):
        with testtools.ExpectedException(exceptions.QuotaNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_quota(self.admin_context, uuid)

    # Server Tests
    def test_create_server(self):
        values = {
            'name': 'ns1.example.org.'
        }

        result = self.storage.create_server(
            self.admin_context, server=objects.Server(**values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])

    def test_create_server_duplicate(self):
        # Create the Initial Server
        self.create_server()

        with testtools.ExpectedException(exceptions.DuplicateServer):
            self.create_server()

    def test_find_servers(self):
        actual = self.storage.find_servers(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single server
        server = self.create_server()

        actual = self.storage.find_servers(self.admin_context)
        self.assertEqual(1, len(actual))
        self.assertEqual(server['name'], actual[0]['name'])

    def test_find_servers_paging(self):
        # Create 10 Servers
        created = [self.create_server(name='ns%d.example.org.' % i)
                   for i in xrange(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_servers)

    def test_find_servers_criterion(self):
        server_one = self.create_server(fixture=0)
        server_two = self.create_server(fixture=1)

        criterion = dict(
            name=server_one['name']
        )

        results = self.storage.find_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_one['name'])

        criterion = dict(
            name=server_two['name']
        )

        results = self.storage.find_servers(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], server_two['name'])

    def test_get_server(self):
        # Create a server
        expected = self.create_server()
        actual = self.storage.get_server(self.admin_context, expected['id'])

        self.assertEqual(str(actual['name']), str(expected['name']))

    def test_get_server_missing(self):
        with testtools.ExpectedException(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_server(self.admin_context, uuid)

    def test_update_server(self):
        # Create a server
        server = self.create_server(name='ns1.example.org.')

        # Update the Object
        server.name = 'ns2.example.org.'

        # Perform the update
        server = self.storage.update_server(self.admin_context, server)

        # Ensure the new value took
        self.assertEqual('ns2.example.org.', server.name)

    def test_update_server_duplicate(self):
        # Create two servers
        server_one = self.create_server(fixture=0)
        server_two = self.create_server(fixture=1)

        # Update the S2 object to be a duplicate of S1
        server_two.name = server_one.name

        with testtools.ExpectedException(exceptions.DuplicateServer):
            self.storage.update_server(self.admin_context, server_two)

    def test_update_server_missing(self):
        server = objects.Server(id='caf771fc-6b05-4891-bee1-c2a48621f57b')
        with testtools.ExpectedException(exceptions.ServerNotFound):
            self.storage.update_server(self.admin_context, server)

    def test_delete_server(self):
        server = self.create_server()

        self.storage.delete_server(self.admin_context, server['id'])

        with testtools.ExpectedException(exceptions.ServerNotFound):
            self.storage.get_server(self.admin_context, server['id'])

    def test_delete_server_missing(self):
        with testtools.ExpectedException(exceptions.ServerNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_server(self.admin_context, uuid)

    # TSIG Key Tests
    def test_create_tsigkey(self):
        values = self.get_tsigkey_fixture()

        result = self.storage.create_tsigkey(
            self.admin_context, tsigkey=objects.TsigKey(**values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['algorithm'], values['algorithm'])
        self.assertEqual(result['secret'], values['secret'])

    def test_create_tsigkey_duplicate(self):
        # Create the Initial TsigKey
        tsigkey_one = self.create_tsigkey()

        values = self.get_tsigkey_fixture(1)
        values['name'] = tsigkey_one['name']

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.create_tsigkey(**values)

    def test_find_tsigkeys(self):
        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single tsigkey
        tsig = self.create_tsigkey()

        actual = self.storage.find_tsigkeys(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(tsig['name'], actual[0]['name'])
        self.assertEqual(tsig['algorithm'], actual[0]['algorithm'])
        self.assertEqual(tsig['secret'], actual[0]['secret'])

    def test_find_tsigkeys_paging(self):
        # Create 10 TSIG Keys
        created = [self.create_tsigkey(name='tsig-%s' % i)
                   for i in xrange(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_tsigkeys)

    def test_find_tsigkeys_criterion(self):
        tsigkey_one = self.create_tsigkey(fixture=0)
        tsigkey_two = self.create_tsigkey(fixture=1)

        criterion = dict(
            name=tsigkey_one['name']
        )

        results = self.storage.find_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_one['name'])

        criterion = dict(
            name=tsigkey_two['name']
        )

        results = self.storage.find_tsigkeys(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], tsigkey_two['name'])

    def test_get_tsigkey(self):
        # Create a tsigkey
        expected = self.create_tsigkey()

        actual = self.storage.get_tsigkey(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['algorithm'], expected['algorithm'])
        self.assertEqual(actual['secret'], expected['secret'])

    def test_get_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_tsigkey(self.admin_context, uuid)

    def test_update_tsigkey(self):
        # Create a tsigkey
        tsigkey = self.create_tsigkey(name='test-key')

        # Update the Object
        tsigkey.name = 'test-key-updated'

        # Perform the update
        tsigkey = self.storage.update_tsigkey(self.admin_context, tsigkey)

        # Ensure the new value took
        self.assertEqual('test-key-updated', tsigkey.name)

    def test_update_tsigkey_duplicate(self):
        # Create two tsigkeys
        tsigkey_one = self.create_tsigkey(fixture=0)
        tsigkey_two = self.create_tsigkey(fixture=1)

        # Update the T2 object to be a duplicate of T1
        tsigkey_two.name = tsigkey_one.name

        with testtools.ExpectedException(exceptions.DuplicateTsigKey):
            self.storage.update_tsigkey(self.admin_context, tsigkey_two)

    def test_update_tsigkey_missing(self):
        tsigkey = objects.TsigKey(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.storage.update_tsigkey(self.admin_context, tsigkey)

    def test_delete_tsigkey(self):
        tsigkey = self.create_tsigkey()

        self.storage.delete_tsigkey(self.admin_context, tsigkey['id'])

        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            self.storage.get_tsigkey(self.admin_context, tsigkey['id'])

    def test_delete_tsigkey_missing(self):
        with testtools.ExpectedException(exceptions.TsigKeyNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_tsigkey(self.admin_context, uuid)

    # Tenant Tests
    def test_find_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 'One'
        two_context = context
        two_context.tenant = 'Two'
        context.all_tenants = True

        # create 3 domains in 2 tenants
        self.create_domain(fixture=0, context=one_context, tenant_id='One')
        domain = self.create_domain(fixture=1, context=one_context,
                                    tenant_id='One')
        self.create_domain(fixture=2, context=two_context, tenant_id='Two')

        # Delete one of the domains.
        self.storage.delete_domain(context, domain['id'])

        # Ensure we get accurate results
        result = self.storage.find_tenants(context)
        result_dict = [dict(t) for t in result]

        expected = [{
            'id': 'One',
            'domain_count': 1,
        }, {
            'id': 'Two',
            'domain_count': 1,
        }]

        self.assertEqual(expected, result_dict)

    def test_get_tenant(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        context.all_tenants = True

        # create 2 domains in a tenant
        domain_1 = self.create_domain(fixture=0, context=one_context)
        domain_2 = self.create_domain(fixture=1, context=one_context)
        domain_3 = self.create_domain(fixture=2, context=one_context)

        # Delete one of the domains.
        self.storage.delete_domain(context, domain_3['id'])

        result = self.storage.get_tenant(context, 1)

        self.assertEqual(result['id'], 1)
        self.assertEqual(result['domain_count'], 2)
        self.assertEqual(sorted(result['domains']),
                         [domain_1['name'], domain_2['name']])

    def test_count_tenants(self):
        context = self.get_admin_context()
        one_context = context
        one_context.tenant = 1
        two_context = context
        two_context.tenant = 2
        context.all_tenants = True

        # in the beginning, there should be nothing
        tenants = self.storage.count_tenants(context)
        self.assertEqual(tenants, 0)

        # create 2 domains with 2 tenants
        self.create_domain(fixture=0, context=one_context, tenant_id=1)
        self.create_domain(fixture=1, context=two_context, tenant_id=2)
        domain = self.create_domain(fixture=2,
                                    context=two_context, tenant_id=2)

        # Delete one of the domains.
        self.storage.delete_domain(context, domain['id'])

        tenants = self.storage.count_tenants(context)
        self.assertEqual(tenants, 2)

    # Domain Tests
    def test_create_domain(self):
        values = {
            'tenant_id': self.admin_context.tenant,
            'name': 'example.net.',
            'email': 'example@example.net'
        }

        result = self.storage.create_domain(
            self.admin_context, domain=objects.Domain(**values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['email'], values['email'])
        self.assertIn('status', result)

    def test_create_domain_duplicate(self):
        # Create the Initial Domain
        self.create_domain()

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.create_domain()

    def test_find_domains(self):
        self.config(quota_domains=20)

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(0, len(actual))

        # Create a single domain
        domain = self.create_domain()

        actual = self.storage.find_domains(self.admin_context)
        self.assertEqual(1, len(actual))

        self.assertEqual(domain['name'], actual[0]['name'])
        self.assertEqual(domain['email'], actual[0]['email'])

    def test_find_domains_paging(self):
        # Create 10 Domains
        created = [self.create_domain(name='example-%d.org.' % i)
                   for i in xrange(10)]

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_domains)

    def test_find_domains_criterion(self):
        domain_one = self.create_domain()
        domain_two = self.create_domain(fixture=1)

        criterion = dict(
            name=domain_one['name']
        )

        results = self.storage.find_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_one['name'])
        self.assertEqual(results[0]['email'], domain_one['email'])
        self.assertIn('status', domain_one)

        criterion = dict(
            name=domain_two['name']
        )

        results = self.storage.find_domains(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['name'], domain_two['name'])
        self.assertEqual(results[0]['email'], domain_two['email'])
        self.assertIn('status', domain_two)

    def test_find_domains_all_tenants(self):
        # Create two contexts with different tenant_id's
        one_context = self.get_admin_context()
        one_context.tenant = 1
        two_context = self.get_admin_context()
        two_context.tenant = 2

        # Create normal and all_tenants context objects
        nm_context = self.get_admin_context()
        at_context = self.get_admin_context()
        at_context.all_tenants = True

        # Create two domains in different tenants
        self.create_domain(fixture=0, context=one_context)
        self.create_domain(fixture=1, context=two_context)

        # Ensure the all_tenants context see's two domains
        results = self.storage.find_domains(at_context)
        self.assertEqual(2, len(results))

        # Ensure the normal context see's no domains
        results = self.storage.find_domains(nm_context)
        self.assertEqual(0, len(results))

        # Ensure the tenant 1 context see's 1 domain
        results = self.storage.find_domains(one_context)
        self.assertEqual(1, len(results))

        # Ensure the tenant 2 context see's 1 domain
        results = self.storage.find_domains(two_context)
        self.assertEqual(1, len(results))

    def test_get_domain(self):
        # Create a domain
        expected = self.create_domain()
        actual = self.storage.get_domain(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['email'], expected['email'])
        self.assertIn('status', actual)

    def test_get_domain_missing(self):
        with testtools.ExpectedException(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_domain(self.admin_context, uuid)

    def test_get_deleted_domain(self):
        context = self.get_admin_context()
        context.show_deleted = True

        domain = self.create_domain(context=context)

        self.storage.delete_domain(context, domain['id'])
        self.storage.get_domain(context, domain['id'])

    def test_find_domain_criterion(self):
        domain_one = self.create_domain()
        domain_two = self.create_domain(fixture=1)

        criterion = dict(
            name=domain_one['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_one['name'])
        self.assertEqual(result['email'], domain_one['email'])
        self.assertIn('status', domain_one)

        criterion = dict(
            name=domain_two['name']
        )

        result = self.storage.find_domain(self.admin_context, criterion)

        self.assertEqual(result['name'], domain_two['name'])
        self.assertEqual(result['email'], domain_two['email'])
        self.assertIn('status', domain_one)
        self.assertIn('status', domain_two)

    def test_find_domain_criterion_missing(self):
        expected = self.create_domain()

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.find_domain(self.admin_context, criterion)

    def test_update_domain(self):
        # Create a domain
        domain = self.create_domain(name='example.org.')

        # Update the Object
        domain.name = 'example.net.'

        # Perform the update
        domain = self.storage.update_domain(self.admin_context, domain)

        # Ensure the new valie took
        self.assertEqual('example.net.', domain.name)

    def test_update_domain_duplicate(self):
        # Create two domains
        domain_one = self.create_domain(fixture=0)
        domain_two = self.create_domain(fixture=1)

        # Update the D2 object to be a duplicate of D1
        domain_two.name = domain_one.name

        with testtools.ExpectedException(exceptions.DuplicateDomain):
            self.storage.update_domain(self.admin_context, domain_two)

    def test_update_domain_missing(self):
        domain = objects.Domain(id='caf771fc-6b05-4891-bee1-c2a48621f57b')
        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.update_domain(self.admin_context, domain)

    def test_delete_domain(self):
        domain = self.create_domain()

        self.storage.delete_domain(self.admin_context, domain['id'])

        with testtools.ExpectedException(exceptions.DomainNotFound):
            self.storage.get_domain(self.admin_context, domain['id'])

    def test_delete_domain_missing(self):
        with testtools.ExpectedException(exceptions.DomainNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_domain(self.admin_context, uuid)

    def test_count_domains(self):
        # in the beginning, there should be nothing
        domains = self.storage.count_domains(self.admin_context)
        self.assertEqual(domains, 0)

        # Create a single domain
        self.create_domain()

        # count 'em up
        domains = self.storage.count_domains(self.admin_context)

        # well, did we get 1?
        self.assertEqual(domains, 1)

    def test_create_recordset(self):
        domain = self.create_domain()

        values = {
            'name': 'www.%s' % domain['name'],
            'type': 'A'
        }

        result = self.storage.create_recordset(
            self.admin_context,
            domain['id'],
            recordset=objects.RecordSet(**values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['name'], values['name'])
        self.assertEqual(result['type'], values['type'])

    def test_create_recordset_duplicate(self):
        domain = self.create_domain()

        # Create the First RecordSet
        self.create_recordset(domain)

        with testtools.ExpectedException(exceptions.DuplicateRecordSet):
            # Attempt to create the second/duplicate recordset
            self.create_recordset(domain)

    def test_create_recordset_with_records(self):
        domain = self.create_domain()

        recordset = objects.RecordSet(
            name='www.%s' % domain['name'],
            type='A',
            records=objects.RecordList(objects=[
                objects.Record(data='192.0.2.1'),
                objects.Record(data='192.0.2.2'),
            ])
        )

        recordset = self.storage.create_recordset(
            self.admin_context, domain['id'], recordset)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

        # Ensure the Records have been saved by checking they have an ID
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_find_recordsets(self):
        domain = self.create_domain()

        criterion = {'domain_id': domain['id']}

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(2, len(actual))

        # Create a single recordset
        recordset_one = self.create_recordset(domain)

        actual = self.storage.find_recordsets(self.admin_context, criterion)
        self.assertEqual(3, len(actual))

        self.assertEqual(recordset_one['name'], actual[2]['name'])
        self.assertEqual(recordset_one['type'], actual[2]['type'])

    def test_find_recordsets_paging(self):
        domain = self.create_domain(name='example.org.')

        # Create 10 RecordSets
        created = [self.create_recordset(domain, name='r-%d.example.org.' % i)
                   for i in xrange(10)]

        # Add in the SOA and NS recordsets that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'domain_id': domain['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'domain_id': domain['id'],
                                                    'type': "NS"})
        created.insert(0, ns)
        created.insert(0, soa)

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_recordsets)

    def test_find_recordsets_criterion(self):
        domain = self.create_domain()

        recordset_one = self.create_recordset(domain, type='A', fixture=0)
        self.create_recordset(domain, fixture=1)

        criterion = dict(
            domain_id=domain['id'],
            name=recordset_one['name'],
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(len(results), 1)

        criterion = dict(
            domain_id=domain['id'],
            type='A',
        )

        results = self.storage.find_recordsets(self.admin_context,
                                               criterion)

        self.assertEqual(len(results), 2)

    def test_find_recordsets_criterion_wildcard(self):
        domain = self.create_domain()

        values = {'name': 'one.%s' % domain['name']}

        self.create_recordset(domain, **values)

        criterion = dict(
            domain_id=domain['id'],
            name="*%s" % domain['name'],
        )

        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Should be 3, as SOA and NS recordsets are automiatcally created
        self.assertEqual(len(results), 3)

    def test_find_recordsets_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            id=recordset.id,
        )

        # Find the RecordSet
        results = self.storage.find_recordsets(self.admin_context, criterion)

        # Ensure we only have one result
        self.assertEqual(1, len(results))

        recordset = results[0]

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_get_recordset(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        actual = self.storage.get_recordset(self.admin_context, expected['id'])

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])

    def test_get_recordset_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_get_recordset_missing(self):
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_recordset(self.admin_context, uuid)

    def test_find_recordset_criterion(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        criterion = dict(
            domain_id=domain['id'],
            name=expected['name'],
        )

        actual = self.storage.find_recordset(self.admin_context, criterion)

        self.assertEqual(actual['name'], expected['name'])
        self.assertEqual(actual['type'], expected['type'])

    def test_find_recordset_criterion_missing(self):
        domain = self.create_domain()
        expected = self.create_recordset(domain)

        criterion = dict(
            name=expected['name'] + "NOT FOUND"
        )

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.find_recordset(self.admin_context, criterion)

    def test_find_recordset_criterion_with_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two Records in the RecordSet
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            id=recordset.id,
        )

        # Fetch the RecordSet again
        recordset = self.storage.find_recordset(self.admin_context, criterion)

        # Ensure recordset.records is a RecordList instance
        self.assertIsInstance(recordset.records, objects.RecordList)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

    def test_update_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        # Update the Object
        recordset.ttl = 1800

        # Perform the update
        recordset = self.storage.update_recordset(self.admin_context,
                                                  recordset)

        # Ensure the new value took
        self.assertEqual(1800, recordset.ttl)

    def test_update_recordset_duplicate(self):
        domain = self.create_domain()

        # Create two recordsets
        recordset_one = self.create_recordset(domain, type='A')
        recordset_two = self.create_recordset(domain, type='A', fixture=1)

        # Update the R2 object to be a duplicate of R1
        recordset_two.name = recordset_one.name

        with testtools.ExpectedException(exceptions.DuplicateRecordSet):
            self.storage.update_recordset(self.admin_context, recordset_two)

    def test_update_recordset_missing(self):
        recordset = objects.RecordSet(
            id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.update_recordset(self.admin_context, recordset)

    def test_update_recordset_with_record_create(self):
        domain = self.create_domain()

        # Create a RecordSet
        recordset = self.create_recordset(domain, 'A')

        # Append two new Records
        recordset.records.append(objects.Record(data='192.0.2.1'))
        recordset.records.append(objects.Record(data='192.0.2.2'))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure two Records are attached to the RecordSet correctly
        self.assertEqual(2, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)
        self.assertIsInstance(recordset.records[1], objects.Record)

        # Ensure the Records have been saved by checking they have an ID
        self.assertIsNotNone(recordset.records[0].id)
        self.assertIsNotNone(recordset.records[1].id)

    def test_update_recordset_with_record_delete(self):
        domain = self.create_domain()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Remove one of the Records
        recordset.records.pop(0)

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure only one Record is attached to the RecordSet
        self.assertEqual(1, len(recordset.records))
        self.assertIsInstance(recordset.records[0], objects.Record)

    def test_update_recordset_with_record_update(self):
        domain = self.create_domain()

        # Create a RecordSet and two Records
        recordset = self.create_recordset(domain, 'A')
        self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Update one of the Records
        updated_record_id = recordset.records[0].id
        recordset.records[0].data = '192.0.2.255'

        # Perform the update
        self.storage.update_recordset(self.admin_context, recordset)

        # Fetch the RecordSet again
        recordset = self.storage.get_recordset(
            self.admin_context, recordset.id)

        # Ensure the Record has been updated
        for record in recordset.records:
            if record.id != updated_record_id:
                continue

            self.assertEqual('192.0.2.255', record.data)
            return  # Exits this test early as we suceeded

        raise Exception('Updated record not found')

    def test_delete_recordset(self):
        domain = self.create_domain()

        # Create a recordset
        recordset = self.create_recordset(domain)

        self.storage.delete_recordset(self.admin_context, recordset['id'])

        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            self.storage.get_recordset(self.admin_context, recordset['id'])

    def test_delete_recordset_missing(self):
        with testtools.ExpectedException(exceptions.RecordSetNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_recordset(self.admin_context, uuid)

    def test_count_recordsets(self):
        # in the beginning, there should be nothing
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 0)

        # Create a single domain & recordset
        domain = self.create_domain()
        self.create_recordset(domain)

        # we should have 3 recordsets now, including SOA & NS
        recordsets = self.storage.count_recordsets(self.admin_context)
        self.assertEqual(recordsets, 3)

    def test_create_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = {
            'data': '192.0.2.1',
        }

        result = self.storage.create_record(self.admin_context,
                                            domain['id'],
                                            recordset['id'],
                                            record=objects.Record(**values))

        self.assertIsNotNone(result['id'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['hash'])
        self.assertIsNone(result['updated_at'])

        self.assertEqual(result['tenant_id'], self.admin_context.tenant)
        self.assertEqual(result['data'], values['data'])
        self.assertIn('status', result)

    def test_create_record_duplicate(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create the First Record
        self.create_record(domain, recordset)

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            # Attempt to create the second/duplicate record
            self.create_record(domain, recordset)

    def test_find_records(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        criterion = {
            'domain_id': domain['id'],
            'recordset_id': recordset['id']
        }

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(0, len(actual))

        # Create a single record
        record = self.create_record(domain, recordset)

        actual = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(1, len(actual))

        self.assertEqual(record['data'], actual[0]['data'])
        self.assertIn('status', record)

    def test_find_records_paging(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        # Create 10 Records
        created = [self.create_record(domain, recordset, data='192.0.2.%d' % i)
                   for i in xrange(10)]

        # Add in the SOA and NS records that are automatically created
        soa = self.storage.find_recordset(self.admin_context,
                                          criterion={'domain_id': domain['id'],
                                                     'type': "SOA"})
        ns = self.storage.find_recordset(self.admin_context,
                                         criterion={'domain_id': domain['id'],
                                                    'type': "NS"})
        for r in ns['records']:
            created.insert(0, r)
        created.append(soa['records'][0])

        # Ensure we can page through the results.
        self._ensure_paging(created, self.storage.find_records)

    def test_find_records_criterion(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        record_one = self.create_record(domain, recordset)
        self.create_record(domain, recordset, fixture=1)

        criterion = dict(
            data=record_one['data'],
            domain_id=domain['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)
        self.assertEqual(len(results), 1)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 2)

    def test_find_records_criterion_wildcard(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        values = {'data': '127.0.0.1'}

        self.create_record(domain, recordset, **values)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
            data="*.0.0.1",
        )

        results = self.storage.find_records(self.admin_context, criterion)

        self.assertEqual(len(results), 1)

    def test_find_records_all_tenants(self):
        # Create two contexts with different tenant_id's
        one_context = self.get_admin_context()
        one_context.tenant = 1
        two_context = self.get_admin_context()
        two_context.tenant = 2

        # Create normal and all_tenants context objects
        nm_context = self.get_admin_context()
        at_context = self.get_admin_context()
        at_context.all_tenants = True

        # Create two domains in different tenants, and 1 record in each
        domain_one = self.create_domain(fixture=0, context=one_context)
        recordset_one = self.create_recordset(domain_one, fixture=0,
                                              context=one_context)
        self.create_record(domain_one, recordset_one, context=one_context)

        domain_two = self.create_domain(fixture=1, context=two_context)
        recordset_one = self.create_recordset(domain_two, fixture=1,
                                              context=two_context)

        self.create_record(domain_two, recordset_one, context=two_context)

        # Ensure the all_tenants context see's two records
        # Plus the SOA & NS in each of 2 domains = 6 records total
        results = self.storage.find_records(at_context)
        self.assertEqual(6, len(results))

        # Ensure the normal context see's no records
        results = self.storage.find_records(nm_context)
        self.assertEqual(0, len(results))

        # Ensure the tenant 1 context see's 1 record + SOA & NS
        results = self.storage.find_records(one_context)
        self.assertEqual(3, len(results))

        # Ensure the tenant 2 context see's 1 record + SOA & NS
        results = self.storage.find_records(two_context)
        self.assertEqual(3, len(results))

    def test_get_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        actual = self.storage.get_record(self.admin_context, expected['id'])

        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_get_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.get_record(self.admin_context, uuid)

    def test_find_record_criterion(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        criterion = dict(
            domain_id=domain['id'],
            recordset_id=recordset['id'],
            data=expected['data'],
        )

        actual = self.storage.find_record(self.admin_context, criterion)

        self.assertEqual(actual['data'], expected['data'])
        self.assertIn('status', actual)

    def test_find_record_criterion_missing(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        expected = self.create_record(domain, recordset)

        criterion = dict(
            domain_id=domain['id'],
            data=expected['data'] + "NOT FOUND",
        )

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.find_record(self.admin_context, criterion)

    def test_update_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain, type='A')

        # Create a record
        record = self.create_record(domain, recordset)

        # Update the Object
        record.data = '192.0.2.255'

        # Perform the update
        record = self.storage.update_record(self.admin_context, record)

        # Ensure the new value took
        self.assertEqual('192.0.2.255', record.data)

    def test_update_record_duplicate(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create two records
        record_one = self.create_record(domain, recordset)
        record_two = self.create_record(domain, recordset, fixture=1)

        # Update the R2 object to be a duplicate of R1
        record_two.data = record_one.data

        with testtools.ExpectedException(exceptions.DuplicateRecord):
            self.storage.update_record(self.admin_context, record_two)

    def test_update_record_missing(self):
        record = objects.Record(id='caf771fc-6b05-4891-bee1-c2a48621f57b')

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.update_record(self.admin_context, record)

    def test_delete_record(self):
        domain = self.create_domain()
        recordset = self.create_recordset(domain)

        # Create a record
        record = self.create_record(domain, recordset)

        self.storage.delete_record(self.admin_context, record['id'])

        with testtools.ExpectedException(exceptions.RecordNotFound):
            self.storage.get_record(self.admin_context, record['id'])

    def test_delete_record_missing(self):
        with testtools.ExpectedException(exceptions.RecordNotFound):
            uuid = 'caf771fc-6b05-4891-bee1-c2a48621f57b'
            self.storage.delete_record(self.admin_context, uuid)

    def test_count_records(self):
        # in the beginning, there should be nothing
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 0)

        # Create a single domain & record
        domain = self.create_domain()
        recordset = self.create_recordset(domain)
        self.create_record(domain, recordset)

        # we should have 1 record now
        records = self.storage.count_records(self.admin_context)
        self.assertEqual(records, 3)

    def test_ping(self):
        pong = self.storage.ping(self.admin_context)

        self.assertEqual(pong['status'], True)
        self.assertIsNotNone(pong['rtt'])
