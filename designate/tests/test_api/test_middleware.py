# Copyright 2012 Managed I.T.
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
from oslo_config import cfg
from oslo_messaging.notify import notifier

from designate.tests.test_api import ApiTestCase
from designate import context
from designate import exceptions
from designate import rpc
from designate.api import middleware


class FakeRequest(object):
    def __init__(self):
        self.headers = {}
        self.environ = {}
        self.GET = {}
        self.POST = {}

    @property
    def params(self):
        data = self.GET.copy()
        data.update(self.POST)
        return data

    def get_response(self, app):
        return "FakeResponse"


class KeystoneContextMiddlewareTest(ApiTestCase):
    def test_process_request(self):
        app = middleware.KeystoneContextMiddleware({})

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin,Member',
        }

        # Process the request
        app.process_request(request)

        self.assertIn('context', request.environ)

        context = request.environ['context']

        self.assertFalse(context.is_admin)
        self.assertEqual('AuthToken', context.auth_token)
        self.assertEqual('UserID', context.user)
        self.assertEqual('TenantID', context.tenant)
        self.assertEqual(['admin', 'Member'], context.roles)

    def test_process_request_invalid_keystone_token(self):
        app = middleware.KeystoneContextMiddleware({})

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': 'TenantID',
            'X-Roles': 'admin,Member',
            'X-Identity-Status': 'Invalid'
        }

        # Process the request
        response = app(request)

        self.assertEqual(401, response.status_code)

    def test_process_unscoped_token(self):
        app = middleware.KeystoneContextMiddleware({})

        request = FakeRequest()

        request.headers = {
            'X-Auth-Token': 'AuthToken',
            'X-User-ID': 'UserID',
            'X-Tenant-ID': None,
            'X-Roles': 'admin,Member',
        }

        # Process the request
        response = app(request)

        self.assertEqual(401, response.status_code)


class NoAuthContextMiddlewareTest(ApiTestCase):
    def test_process_request(self):
        app = middleware.NoAuthContextMiddleware({})

        request = FakeRequest()

        # Process the request
        app.process_request(request)

        self.assertIn('context', request.environ)

        ctxt = request.environ['context']

        self.assertIsNone(ctxt.auth_token)
        self.assertEqual('noauth-user', ctxt.user)
        self.assertEqual('noauth-project', ctxt.tenant)
        self.assertEqual(['admin'], ctxt.roles)


class MaintenanceMiddlewareTest(ApiTestCase):
    def test_process_request_disabled(self):
        self.config(maintenance_mode=False, group='service:api')

        request = FakeRequest()
        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was not blocked
        self.assertEqual(response, 'FakeResponse')

    def test_process_request_enabled_reject(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = context.DesignateContext(roles=['user'])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(503, response.status_code)

    def test_process_request_enabled_reject_no_roles(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = context.DesignateContext(roles=[])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(503, response.status_code)

    def test_process_request_enabled_reject_no_context(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was blocked
        self.assertEqual(503, response.status_code)

    def test_process_request_enabled_bypass(self):
        self.config(maintenance_mode=True, maintenance_mode_role='admin',
                    group='service:api')

        request = FakeRequest()
        request.environ['context'] = context.DesignateContext(roles=['admin'])

        app = middleware.MaintenanceMiddleware({})

        # Process the request
        response = app(request)

        # Ensure request was not blocked
        self.assertEqual('FakeResponse', response)


class NormalizeURIMiddlewareTest(ApiTestCase):
    def test_strip_trailing_slases(self):
        request = FakeRequest()
        request.environ['PATH_INFO'] = 'resource/'

        app = middleware.NormalizeURIMiddleware({})

        # Process the request
        app(request)

        # Ensure request's PATH_INFO had the trailing slash removed.
        self.assertEqual('resource', request.environ['PATH_INFO'])

    def test_strip_trailing_slases_multiple(self):
        request = FakeRequest()
        request.environ['PATH_INFO'] = 'resource///'

        app = middleware.NormalizeURIMiddleware({})

        # Process the request
        app(request)

        # Ensure request's PATH_INFO had the trailing slash removed.
        self.assertEqual('resource', request.environ['PATH_INFO'])


class FaultMiddlewareTest(ApiTestCase):
    @mock.patch.object(notifier.Notifier, "error")
    def test_notify_of_fault(self, mock_notifier):
        self.config(notify_api_faults=True)
        rpc.init(cfg.CONF)
        app = middleware.FaultWrapperMiddleware({})

        class RaisingRequest(FakeRequest):
            def get_response(self, request):
                raise exceptions.DuplicateZone()

        request = RaisingRequest()
        ctxt = context.DesignateContext()
        ctxt.request_id = 'one'
        request.environ['context'] = ctxt

        # Process the request
        app(request)

        self.assertEqual(1, mock_notifier.call_count)
        mock_notifier.call_args(
            ctxt,
            'dns.api.fault',
            {"url": None, "status": 409, "exception": ""})
