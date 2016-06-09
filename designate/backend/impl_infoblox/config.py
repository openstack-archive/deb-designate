# Copyright 2015 Infoblox Inc.
# All Rights Reserved.
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
from oslo_log import log

LOG = log.getLogger(__name__)


cfg.CONF.register_group(cfg.OptGroup(
    name='backend:infoblox', title="Configuration for Infoblox Backend"
))

OPTS = [
    cfg.StrOpt(
        'wapi_url',
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.StrOpt(
        'username',
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.StrOpt(
        'password',
        deprecated_for_removal=True,
        secret=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.BoolOpt(
        'sslverify',
        default=True,
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.BoolOpt(
        'multi_tenant',
        default=False,
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.IntOpt(
        'http_pool_connections',
        default=100,
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.IntOpt(
        'http_pool_maxsize',
        default=100,
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.StrOpt(
        'dns_view',
        default='default',
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.StrOpt(
        'network_view',
        default='default',
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file"),
    cfg.StrOpt(
        'ns_group',
        deprecated_for_removal=True,
        deprecated_reason="All backend options have been migrated to options "
        "in the pools.yaml file")
]

cfg.CONF.register_opts(OPTS, group='backend:infoblox')
