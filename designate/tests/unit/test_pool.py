# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
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

from oslo_log import log as logging
import oslotest.base

from designate import objects

LOG = logging.getLogger(__name__)


def create_test_pool():
    return objects.Pool(
        name='pool1',
        description='desc',
    )


class RoObject(dict):
    def __setitem__(self, *a):
        raise NotImplementedError

    def __setattr__(self, *a):
        raise NotImplementedError

    def __getattr__(self, k):
        return self[k]


mock_conf = RoObject(**{
    'host': 'foohost',
    'pool:1': RoObject(
        targets=['t1', 't2'],
        nameservers=['pt1', 'pt2'],
        also_notifies=['1.0.0.0:1', '2.0.0.0:2']
    ),
    'pool_nameserver:pt1': RoObject(
        host='pool_host_1',
        port=123
    ),
    'pool_nameserver:pt2': RoObject(
        host='pool_host_2',
        port=456
    ),
    'pool_target:t1': RoObject(
        type='t1',
        masters=[],
        options=dict(a=1, b=2),
    ),
    'pool_target:t2': RoObject(
        type='t2',
        masters=['1.1.1.1:11'],
        options={},
    ),
})


def deep_sort_lists(obj):
    """Sort lists nested in dictionaries
    """
    if isinstance(obj, dict):
        return {k: deep_sort_lists(obj[k]) for k in obj}

    if isinstance(obj, list):
        return [deep_sort_lists(v) for v in sorted(obj)]

    return obj


class poolTest(oslotest.base.BaseTestCase):

    def test_init_from_config(self):
        pool = objects.Pool.from_config(mock_conf, '1')
        expected = {'also_notifies': [{'host': '1.0.0.0', 'port': 1},
                                      {'host': '2.0.0.0', 'port': 2}],
                    'description': 'Pool built from configuration on foohost',
                    'id': '1',
                    'nameservers': [{'host': 'pool_host_1',
                                     'id': 'pt1',
                                     'port': 123},
                                    {'host': 'pool_host_2',
                                     'id': 'pt2',
                                     'port': 456}],
                    'targets': [{'id': 't1',
                                 'masters': [],
                                 'options': [{'key': 'a', 'value': 1},
                                             {'key': 'b', 'value': 2}],
                                 'type': 't1'},
                                {'id': 't2',
                                 'masters': [{'host': '1.1.1.1', 'port': 11}],
                                 'options': [],
                                 'type': 't2'}]}

        actual = deep_sort_lists(pool.to_dict())
        self.assertEqual(actual, expected)
