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


class PoolTarget(base.DictObjectMixin, base.PersistentObjectMixin,
                 base.DesignateObject):
    FIELDS = {
        'pool_id': {
            'schema': {
                'type': 'string',
                'description': 'Pool identifier',
                'format': 'uuid',
            },
        },
        'type': {},
        'tsigkey_id': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'TSIG identifier',
                'format': 'uuid',
            },
        },
        'description': {
            'schema': {
                'type': ['string', 'null'],
                'description': 'Description for the pool',
                'maxLength': 160
            }
        },
        'masters': {
            'relation': True,
            'relation_cls': 'PoolTargetMasterList'
        },
        'options': {
            'relation': True,
            'relation_cls': 'PoolTargetOptionList'
        },
        'backend': {}
    }

    STRING_KEYS = [
        'id', 'type', 'pool_id'
    ]


class PoolTargetList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolTarget
