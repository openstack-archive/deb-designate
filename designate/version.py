# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import pbr.version

DESIGNATE_VENDOR = "OpenStack Foundation"
DESIGNATE_PRODUCT = "OpenStack Designate"

version_info = pbr.version.VersionInfo('designate')


def vendor_string():
    return DESIGNATE_VENDOR


def product_string():
    return DESIGNATE_PRODUCT


def package_string():
    return None


def version_string_with_package():
    if package_string() is None:
        return version_info.version_string()
    else:
        return "%s-%s" % (version_info.version_string(), package_string())
