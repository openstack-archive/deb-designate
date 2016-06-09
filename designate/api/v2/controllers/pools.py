# Copyright (c) 2014 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import pecan
from oslo_log import log as logging

from designate import utils
from designate.i18n import _LW
from designate.api.v2.controllers import rest
from designate.objects import Pool
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI


LOG = logging.getLogger(__name__)


class PoolsController(rest.RestController):
    SORT_KEYS = ['created_at', 'id', 'updated_at', 'name']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('pool_id')
    def get_one(self, pool_id):
        """Get the specific Pool"""
        request = pecan.request
        context = request.environ['context']

        pool = self.central_api.get_pool(context, pool_id)

        LOG.info(_LI("Retrieved %(pool)s"), {'pool': pool})

        return DesignateAdapter.render('API_v2', pool, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List all Pools"""
        request = pecan.request
        context = request.environ['context']

        # Extract the pagination params
        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('name', )
        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        pools = self.central_api.find_pools(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(pools)s"), {'pools': pools})

        return DesignateAdapter.render('API_v2', pools, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create a Pool"""

        LOG.warning(_LW("Use of this API Method is DEPRICATED. This will have "
                        "unforseen side affects when used with the "
                        "designate-manage pool commands"))

        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        body = request.body_dict

        pool = DesignateAdapter.parse('API_v2', body, Pool())

        pool.validate()

        # Create the pool
        pool = self.central_api.create_pool(context, pool)

        LOG.info(_LI("Created %(pool)s"), {'pool': pool})

        pool = DesignateAdapter.render('API_v2', pool, request=request)
        response.status_int = 201

        response.headers['Location'] = pool['links']['self']

        # Prepare and return the response body
        return pool

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('pool_id')
    def patch_one(self, pool_id):
        """Update the specific pool"""

        LOG.warning(_LW("Use of this API Method is DEPRICATED. This will have "
                        "unforseen side affects when used with the "
                        "designate-manage pool commands"))

        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')

        # Fetch the existing pool
        pool = self.central_api.get_pool(context, pool_id)

        pool = DesignateAdapter.parse('API_v2', body, pool)

        pool.validate()

        pool = self.central_api.update_pool(context, pool)

        LOG.info(_LI("Updated %(pool)s"), {'pool': pool})

        response.status_int = 202

        return DesignateAdapter.render('API_v2', pool, request=request)

    @pecan.expose(template=None, content_type='application/json')
    @utils.validate_uuid('pool_id')
    def delete_one(self, pool_id):
        """Delete the specific pool"""

        LOG.warning(_LW("Use of this API Method is DEPRICATED. This will have "
                        "unforseen side affects when used with the "
                        "designate-manage pool commands"))

        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        pool = self.central_api.delete_pool(context, pool_id)

        LOG.info(_LI("Deleted %(pool)s"), {'pool': pool})

        response.status_int = 204

        # NOTE: This is a hack and a half.. But Pecan needs it.
        return ''
