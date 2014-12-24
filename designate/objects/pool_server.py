# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebaysf.com>
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
from designate.objects import base


# TODO(Ron): replace the Server object with this object.
class PoolServer(base.DictObjectMixin, base.DesignateObject):
    FIELDS = {
        'id': {},
        'host': {},
        'port': {},
        'backend': {},
        'backend_options': {},
        'tsig_key': {}
    }


class PoolServerList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = PoolServer
