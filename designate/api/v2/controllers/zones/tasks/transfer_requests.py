# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Graham Hayes <graham.hayes@hp.com>
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
import six
import pecan
from oslo_log import log as logging

from designate import utils
from designate.api.v2.controllers import rest
from designate.objects import ZoneTransferRequest
from designate.objects.adapters import DesignateAdapter
LOG = logging.getLogger(__name__)


class TransferRequestsController(rest.RestController):

    SORT_KEYS = ['created_at', 'id', 'updated_at']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('transfer_request_id')
    def get_one(self, transfer_request_id):
        """Get transfer_request"""

        request = pecan.request
        context = request.environ['context']

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.get_zone_transfer_request(
                context, transfer_request_id),
            request=request,
            context=context)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List ZoneTransferRequests"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            params, self.SORT_KEYS)

        # Extract any filter params.
        criterion = self._apply_filter_params(params, ('status',), {})

        return DesignateAdapter.render(
            'API_v2',
            self.central_api.find_zone_transfer_requests(
                context, criterion, marker, limit, sort_key, sort_dir),
            request=request,
            context=context)

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('zone_id')
    def post_all(self, zone_id):
        """Create ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        try:
            body = request.body_dict
        except Exception as e:
            if six.text_type(e) != 'TODO: Unsupported Content Type':
                raise
            else:
                # Got a blank body
                body = dict()

        body['zone_id'] = zone_id

        zone_transfer_request = DesignateAdapter.parse(
            'API_v2', body, ZoneTransferRequest())

        zone_transfer_request.validate()

        # Create the zone_transfer_request
        zone_transfer_request = self.central_api.create_zone_transfer_request(
            context, zone_transfer_request)
        response.status_int = 201

        zone_transfer_request = DesignateAdapter.render(
            'API_v2', zone_transfer_request, request=request, context=context)

        response.headers['Location'] = zone_transfer_request['links']['self']
        # Prepare and return the response body
        return zone_transfer_request

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('zone_transfer_request_id')
    def patch_one(self, zone_transfer_request_id):
        """Update ZoneTransferRequest"""
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')

        # Fetch the existing zone_transfer_request
        zone_transfer_request = self.central_api.get_zone_transfer_request(
            context, zone_transfer_request_id)

        zone_transfer_request = DesignateAdapter.parse(
            'API_v2', body, zone_transfer_request)

        zone_transfer_request.validate()

        zone_transfer_request = self.central_api.update_zone_transfer_request(
            context, zone_transfer_request)

        response.status_int = 200

        return DesignateAdapter.render(
            'API_v2', zone_transfer_request, request=request, context=context)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('zone_transfer_request_id')
    def delete_one(self, zone_transfer_request_id):
        """Delete ZoneTransferRequest"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        self.central_api.delete_zone_transfer_request(
            context, zone_transfer_request_id)

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
