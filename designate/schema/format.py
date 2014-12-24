# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hp.com>
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
import re

import jsonschema
from jsonschema import compat
import netaddr

from designate.openstack.common import log as logging


LOG = logging.getLogger(__name__)

RE_DOMAINNAME = r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)\.)+$'
RE_HOSTNAME = r'^(?!.{255,})(?:(?:^\*|(?!\-)[A-Za-z0-9_\-]{1,63})(?<!\-)\.)+$'

# The TLD name will not end in a period.
RE_TLDNAME = r'^(?!.{255,})(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-))' \
             r'(?:\.(?:(?!\-)[A-Za-z0-9_\-]{1,63}(?<!\-)))*$'

RE_UUID = r'^(?:[0-9a-fA-F]){8}-(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){4}-' \
          r'(?:[0-9a-fA-F]){4}-(?:[0-9a-fA-F]){12}$'

draft3_format_checker = jsonschema.draft3_format_checker
draft4_format_checker = jsonschema.draft4_format_checker


@draft3_format_checker.checks("ip-address")
@draft4_format_checker.checks("ipv4")
def is_ipv4(instance):
    if not isinstance(instance, compat.str_types):
        return True

    try:
        address = netaddr.IPAddress(instance, version=4)
        # netaddr happly accepts, and expands "127.0" into "127.0.0.0"
        if str(address) != instance:
            return False
    except Exception:
        return False

    if instance == '0.0.0.0':  # RFC5735
        return False

    return True


@draft3_format_checker.checks("ipv6")
@draft4_format_checker.checks("ipv6")
def is_ipv6(instance):
    if not isinstance(instance, compat.str_types):
        return True

    try:
        netaddr.IPAddress(instance, version=6)
    except Exception:
        return False

    return True


@draft3_format_checker.checks("host-name")
@draft4_format_checker.checks("hostname")
def is_hostname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_HOSTNAME, instance):
        return False

    return True


@draft3_format_checker.checks("domain-name")
@draft4_format_checker.checks("domainname")
def is_domainname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_DOMAINNAME, instance):
        return False

    return True


@draft3_format_checker.checks("tld-name")
@draft4_format_checker.checks("tldname")
def is_tldname(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_TLDNAME, instance):
        return False

    return True


@draft3_format_checker.checks("email")
@draft4_format_checker.checks("email")
def is_email(instance):
    if not isinstance(instance, compat.str_types):
        return True

    # A valid email address. We use the RFC1035 version of "valid".
    if instance.count('@') != 1:
        return False

    rname = instance.replace('@', '.', 1)

    if not re.match(RE_DOMAINNAME, "%s." % rname):
        return False

    return True


@draft3_format_checker.checks("uuid")
@draft4_format_checker.checks("uuid")
def is_uuid(instance):
    if not isinstance(instance, compat.str_types):
        return True

    if not re.match(RE_UUID, instance):
        return False

    return True
