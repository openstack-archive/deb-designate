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
from designate.objects import base


class PoolTargetOption(base.DictObjectMixin, base.PersistentObjectMixin,
                       base.DesignateObject):
    FIELDS = {
        'pool_target_id': {
            'schema': {
                'type': 'string',
                'description': 'Pool Target identifier',
                'format': 'uuid',
            },
        },
        'key': {
            'schema': {
                'type': 'string',
                'maxLength': 255,
            },
            'required': True,
        },
        'value': {
            'schema': {
                'type': 'string',
                'maxLength': 255,
            },
            'required': True
        }
    }

    STRING_KEYS = [
        'id', 'key', 'value', 'pool_target_id'
    ]


class PoolTargetOptionList(base.AttributeListObjectMixin,
                           base.DesignateObject):
    LIST_ITEM_TYPE = PoolTargetOption
