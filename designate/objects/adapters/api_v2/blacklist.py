# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from designate.objects.adapters.api_v2 import base
from designate import objects


class BlacklistAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Blacklist

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "pattern": {
                'read_only': False
            },
            "description": {
                'read_only': False
            },
            "created_at": {},
            "updated_at": {},
        },
        'options': {
            'links': True,
            'resource_name': 'blacklist',
            'collection_name': 'blacklists',
        }
    }


class BlacklistListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.BlacklistList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'blacklist',
            'collection_name': 'blacklists',
        }
    }
