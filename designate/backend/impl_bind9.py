# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebay.com>
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

"""
Bind 9 backend. Create and delete zones by executing rndc
"""

import random

import six
from oslo_log import log as logging
from oslo_utils import strutils

from designate import exceptions
from designate import utils
from designate.backend import base


LOG = logging.getLogger(__name__)
DEFAULT_MASTER_PORT = 5354


class Bind9Backend(base.Backend):
    __plugin_name__ = 'bind9'

    __backend_status__ = 'integrated'

    def __init__(self, target):
        super(Bind9Backend, self).__init__(target)

        # TODO(Federico): make attributes private, run _rndc_base at init time
        self.host = self.options.get('host', '127.0.0.1')
        self.port = int(self.options.get('port', 53))
        self.view = self.options.get('view')
        self.rndc_host = self.options.get('rndc_host', '127.0.0.1')
        self.rndc_port = int(self.options.get('rndc_port', 953))
        self.rndc_config_file = self.options.get('rndc_config_file')
        self.rndc_key_file = self.options.get('rndc_key_file')

        # Removes zone files when a zone is deleted.
        # This option will take effect on bind>=9.10.0.
        self.clean_zonefile = strutils.bool_from_string(
                                  self.options.get('clean_zonefile', 'false'))

    def create_zone(self, context, zone):
        """Create a new Zone by executin rndc, then notify mDNS
        Do not raise exceptions if the zone already exists.
        """
        LOG.debug('Create Zone')
        masters = []
        for master in self.masters:
            host = master['host']
            port = master['port']
            masters.append('%s port %s' % (host, port))

        # Ensure different MiniDNS instances are targeted for AXFRs
        random.shuffle(masters)

        if self.view:
            view = 'in %s' % self.view
        else:
            view = ''

        rndc_op = [
            'addzone',
            '%s %s { type slave; masters { %s;}; file "slave.%s%s"; };' %
            (zone['name'].rstrip('.'), view, '; '.join(masters), zone['name'],
             zone['id']),
        ]

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If create fails because the zone exists, don't reraise
            if "already exists" not in six.text_type(e):
                raise

        self.mdns_api.notify_zone_changed(
            context, zone, self.host, self.port, self.timeout,
            self.retry_interval, self.max_retries, self.delay)

    def delete_zone(self, context, zone):
        """Delete a new Zone by executin rndc
        Do not raise exceptions if the zone does not exist.
        """
        LOG.debug('Delete Zone')

        if self.view:
            view = 'in %s' % self.view
        else:
            view = ''

        rndc_op = [
            'delzone',
            '%s %s' % (zone['name'].rstrip('.'), view),
        ]
        if self.clean_zonefile:
            rndc_op.insert(1, '-clean')

        try:
            self._execute_rndc(rndc_op)
        except exceptions.Backend as e:
            # If zone is already deleted, don't reraise
            if "not found" not in six.text_type(e):
                raise

    def _rndc_base(self):
        rndc_call = [
            'rndc',
            '-s', self.rndc_host,
            '-p', str(self.rndc_port),
        ]

        if self.rndc_config_file:
            rndc_call.extend(
                ['-c', self.rndc_config_file])

        if self.rndc_key_file:
            rndc_call.extend(
                ['-k', self.rndc_key_file])

        return rndc_call

    def _execute_rndc(self, rndc_op):
        try:
            rndc_call = self._rndc_base()
            rndc_call.extend(rndc_op)
            LOG.debug('Executing RNDC call: %s' % " ".join(rndc_call))
            utils.execute(*rndc_call)
        except utils.processutils.ProcessExecutionError as e:
            LOG.debug('RNDC call failure: %s' % e)
            raise exceptions.Backend(e)
