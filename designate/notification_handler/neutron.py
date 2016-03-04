# Copyright 2012 Bouvet ASA
#
# Author: Endre Karlson <endre.karlson@bouvet.no>
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
from oslo_config import cfg
from oslo_log import log as logging

from designate.notification_handler.base import BaseAddressHandler


LOG = logging.getLogger(__name__)

cfg.CONF.register_group(cfg.OptGroup(
    name='handler:neutron_floatingip',
    title="Configuration for Neutron Notification Handler"
))

cfg.CONF.register_opts([
    cfg.ListOpt('notification-topics', default=['notifications']),
    cfg.StrOpt('control-exchange', default='neutron'),
    cfg.StrOpt('zone-id'),
    cfg.MultiStrOpt('format', default=[
                    '%(octet0)s-%(octet1)s-%(octet2)s-%(octet3)s.%(zone)s'])
], group='handler:neutron_floatingip')


class NeutronFloatingHandler(BaseAddressHandler):
    """Handler for Neutron's notifications"""
    __plugin_name__ = 'neutron_floatingip'

    def get_exchange_topics(self):
        exchange = cfg.CONF[self.name].control_exchange

        topics = [topic for topic in cfg.CONF[self.name].notification_topics]

        return (exchange, topics)

    def get_event_types(self):
        return [
            'floatingip.update.end',
            'floatingip.delete.start'
        ]

    def process_notification(self, context, event_type, payload):
        LOG.debug('%s received notification - %s',
                  self.get_canonical_name(), event_type)

        zone_id = cfg.CONF[self.name].zone_id
        if event_type.startswith('floatingip.delete'):
            self._delete(zone_id=zone_id,
                         resource_id=payload['floatingip_id'],
                         resource_type='floatingip')
        elif event_type.startswith('floatingip.update'):
            if payload['floatingip']['fixed_ip_address']:
                address = {
                    'version': 4,
                    'address': payload['floatingip']['floating_ip_address']
                }
                payload['floatingip']['project'] = getattr(
                    context, 'tenant', None)
                self._create(addresses=[address],
                             extra=payload['floatingip'],
                             zone_id=zone_id,
                             resource_id=payload['floatingip']['id'],
                             resource_type='floatingip')
            else:
                self._delete(zone_id=zone_id,
                             resource_id=payload['floatingip']['id'],
                             resource_type='floatingip')
